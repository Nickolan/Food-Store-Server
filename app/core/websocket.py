# =============================================================================
# CONNECTION MANAGER — WebSocket con Rooms por Rol y por Pedido
# =============================================================================
#
# Este módulo implementa el gestor de conexiones WebSocket del sistema,
# utilizando una arquitectura híbrida de "rooms" (salas) para dirigir
# los eventos en tiempo real de forma selectiva y escalable.
#
# ─── ARQUITECTURA ─────────────────────────────────────────────────────────────
#
# El sistema usa DOS tipos de rooms:
#
#   1. ROOMS POR ROL (role:{rol})
#      - Cada empleado se une a la room de su rol al conectarse
#      - Ejemplos: role:cocina, role:pedidos, role:admin, role:user
#      - Ventaja: el cajero ve TODOS los pedidos entrantes, la cocina ve
#        su cola completa, sin necesidad de mover sockets entre rooms
#
#   2. ROOMS POR PEDIDO (order:{orderId})
#      - Cada cliente se suscribe a la room de SU pedido específico
#      - Solo recibe actualizaciones de ese pedido en particular
#      - Ventaja: privacidad — un cliente no puede espiar pedidos ajenos
#
# ─── FLUJO DE VIDA ────────────────────────────────────────────────────────────
#
#   CONEXIÓN:
#     1. Frontend abre WebSocket → handshake con cookie HttpOnly
#     2. Backend valida JWT (firma + expiración)
#     3. Backend busca usuario en BD (existe + activo)
#     4. Se ejecuta manager.connect(websocket, role, user_id)
#     5. El socket se une automáticamente a "role:{rol}"
#     6. Si es staff (admin/pedidos/cocina), recibe todos los eventos de su rol
#     7. Si es cliente (user), puede suscribirse a pedidos específicos
#
#   SUSCRIPCIÓN A PEDIDO (solo clientes):
#     1. Cliente envía: {"action": "subscribe-order", "order_id": 5}
#     2. Backend valida que el pedido pertenece al usuario
#     3. Se ejecuta manager.join_order_room(websocket, order_id)
#     4. El socket se une a "order:5"
#     5. Ahora recibe eventos de ese pedido específico
#
#   DESUSCRIPCIÓN:
#     1. Cliente envía: {"action": "unsubscribe-order", "order_id": 5}
#     2. Se ejecuta manager.leave_order_room(websocket, order_id)
#     3. El socket sale de "order:5"
#
#   DESCONEXIÓN:
#     1. Se detecta WebSocketDisconnect
#     2. Se ejecuta manager.disconnect(websocket)
#     3. Se remueve el socket de TODAS las rooms a las que pertenecía
#     4. Si una room queda vacía, se elimina del mapa
#
# ─── EMISIÓN DE EVENTOS ────────────────────────────────────────────────────────
#
# Cuando un pedido cambia de estado (FSM), el service emite eventos a:
#
#   1. La room del pedido:  manager.broadcast_to_order(order_id, event, data)
#      → El cliente que hizo el pedido recibe la actualización
#
#   2. Las rooms de rol:   manager.broadcast_to_roles([...], event, data)
#      → El personal relevante recibe la actualización
#
# Ejemplo: pedido pasa de "pendiente" a "confirmado"
#   → broadcast_to_order(5, "PEDIDO_CONFIRMADO", pedido_data)
#   → broadcast_to_roles(["pedidos", "cocina"], "PEDIDO_CONFIRMADO", pedido_data)
#
# ─── SEGURIDAD ─────────────────────────────────────────────────────────────────
#
#   - El JWT se lee EXCLUSIVAMENTE de la cookie HttpOnly (no del header)
#   - Los clientes solo pueden suscribirse a pedidos que les pertenecen
#   - El backend valida la propiedad del pedido contra la BD
#   - Las rooms son volátiles; al reconectar, el frontend debe hacer
#     fetch inicial de pedidos activos desde la API REST
#
# ─── FORMATO DE MENSAJES WebSocket ─────────────────────────────────────────────
#
#   Cliente → Backend:
#     {"action": "subscribe-order",   "order_id": 5}
#     {"action": "unsubscribe-order", "order_id": 5}
#
#   Backend → Cliente:
#     {"event": "PEDIDO_CONFIRMADO",     "data": {...pedido...}}
#     {"event": "PEDIDO_EN_PREPARACION", "data": {...pedido...}}
#     {"event": "PEDIDO_EN_CAMINO",      "data": {...pedido...}}
#     {"event": "PEDIDO_CANCELADO",      "data": {...pedido...}}
#     {"event": "PEDIDO_ENTREGADO",      "data": {...pedido...}}
#     {"event": "SUBSCRIBED",            "data": {"order_id": 5}}
#     {"event": "ERROR",                 "data": {"detail": "..."}}
#
# =============================================================================

import logging
from typing import Any
from fastapi import WebSocket

# Logger del módulo para trazabilidad de eventos WebSocket
logger = logging.getLogger("app.core.websocket")


class ConnectionManager:
    """
    Gestor de conexiones WebSocket con soporte de rooms por rol y por pedido.

    Mantiene dos estructuras de datos principales:
      - rooms:         qué sockets hay en cada room
      - socket_rooms:  a qué rooms pertenece cada socket (mapa inverso)

    El mapa inverso es fundamental para la limpieza en desconexión:
    cuando un socket se desconoce, saber exactamente a qué rooms pertenecía
    permite removerlo de todas sin recorrer todas las rooms.
    """

    def __init__(self) -> None:
        # ─── Estructura principal: rooms ──────────────────────────────────────
        # Mapa de room_name → set de conexiones WebSocket en esa room.
        #
        # Ejemplo de estado en memoria:
        #   {
        #     "role:cocina":  {ws_cocinero1, ws_cocinero2},
        #     "role:pedidos": {ws_cajero1},
        #     "order:5":      {ws_cliente_juan},
        #     "order:12":     {ws_cliente_maria},
        #   }
        #
        # Cada room es un set para evitar duplicados (un socket no puede estar
        # dos veces en la misma room).
        self.rooms: dict[str, set[WebSocket]] = {}

        # ─── Mapa inverso: socket_rooms ──────────────────────────────────────
        # Mapa de WebSocket → set de room_names donde está ese socket.
        #
        # Ejemplo:
        #   {
        #     ws_cocinero1: {"role:cocina"},
        #     ws_cajero1:   {"role:pedidos", "role:admin"},
        #     ws_cliente_juan: {"role:user", "order:5"},
        #   }
        #
        # Se usa para:
        #   1. Saber a qué rooms limpiar al desconectar un socket
        #   2. Evitar enviar el mismo evento dos veces a un socket que esté
        #      en múltiples rooms (ej: admin en role:admin + role:pedidos)
        self.socket_rooms: dict[WebSocket, set[str]] = {}

    # =========================================================================
    # CONEXIÓN / DESCONEXIÓN
    # =========================================================================

    async def connect(self, websocket: WebSocket, role: str, user_id: int) -> None:
        """
        Acepta el handshake WebSocket y registra la conexión en la room de su rol.

        Este método es el punto de entrada después de que el router validó
        el JWT y obtuvo el rol del usuario. No valida credenciales — eso
        ya se hizo en el handshake del router.

        Args:
            websocket: La conexión WebSocket del cliente
            role:      El rol del usuario (ej: "cocina", "pedidos", "admin", "user")
            user_id:   ID numérico del usuario (para logs)

        Flujo:
          1. Acepta el handshake HTTP→WebSocket
          2. Normaliza el rol a minúsculas para consistencia en nombres de room
          3. Une el socket a "role:{rol}" via _join_room()
          4. Registra en logs para trazabilidad
        """
        await websocket.accept()

        # Normalizar rol a minúsculas para consistencia en nombres de room
        # "COCINA" → "role:cocina", "Admin" → "role:admin"
        role_key = f"role:{role.lower()}"

        # Unir el socket a su room de rol
        self._join_room(websocket, role_key)

        logger.info(
            f"Conexión WebSocket aceptada. user_id={user_id}, role={role}, "
            f"room={role_key}. Total rooms activas: {len(self.rooms)}"
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Elimina un socket de TODAS las rooms a las que pertenezca.

        Este método se llama cuando:
          - El cliente cierra la pestaña/navegador
          - Se pierde la conexión de red
          - Se detecta un error en la conexión

        Flujo:
          1. Obtener todas las rooms del socket del mapa inverso
          2. Para cada room, remover el socket del set
          3. Si la room queda vacía, eliminarla del mapa (liberar memoria)
          4. Eliminar la entrada del mapa inverso

        No lanza excepciones — usa discard() en lugar de remove() para
        que no falle si el socket ya no está en alguna room.
        """
        # Obtener y eliminar del mapa inverso
        rooms = self.socket_rooms.pop(websocket, set())

        # Remover de cada room
        for room in rooms:
            if room in self.rooms:
                self.rooms[room].discard(websocket)
                # Si la room quedó vacía, eliminarla para no acumular rooms huérfanas
                if not self.rooms[room]:
                    del self.rooms[room]

        logger.info(
            f"Conexión WebSocket finalizada. Rooms liberadas: {rooms}. "
            f"Total rooms activas: {len(self.rooms)}"
        )

    # =========================================================================
    # GESTIÓN DE ROOMS POR PEDIDO (para clientes)
    # =========================================================================

    def join_order_room(self, websocket: WebSocket, order_id: int) -> None:
        """
        Suscribe un socket a la room de un pedido específico.

        Solo los clientes (role:user) deberían usar esto. El router
        valida la propiedad del pedido antes de llamar a este método.

        Args:
            websocket: La conexión del cliente
            order_id:  ID del pedido al que quiere suscribirse

        Ejemplo:
          join_order_room(ws_cliente, 5)  →  socket se une a "order:5"
        """
        room = f"order:{order_id}"
        self._join_room(websocket, room)
        logger.info(f"Socket suscrito a room {room}")

    def leave_order_room(self, websocket: WebSocket, order_id: int) -> None:
        """
        Desuscribe un socket de la room de un pedido.

        Útil cuando:
          - El cliente ya no quiere seguir un pedido
          - El pedido llegó a estado terminal (entregado/cancelado)
          - Se quiere limpiar suscripciones manualmente

        Args:
            websocket: La conexión del cliente
            order_id:  ID del pedido del que quiere desuscribirse
        """
        room = f"order:{order_id}"
        if room in self.rooms:
            self.rooms[room].discard(websocket)
            if websocket in self.socket_rooms:
                self.socket_rooms[websocket].discard(room)
            # Si la room quedó vacía, eliminarla
            if not self.rooms[room]:
                del self.rooms[room]

    # =========================================================================
    # EMISIÓN DE EVENTOS
    # =========================================================================

    async def broadcast_to_role(self, role: str, event_type: str, data: dict[str, Any]) -> None:
        """
        Envía un evento a TODOS los sockets en la room de un rol específico.

        Ejemplo:
          broadcast_to_role("cocina", "PEDIDO_CONFIRMADO", pedido_data)
          → todos los cocineros conectados reciben el evento

        Args:
            role:      Nombre del rol (se normaliza a minúsculas)
            event_type: Tipo de evento (ej: "PEDIDO_CONFIRMADO")
            data:      Datos del pedido (diccionario serializable a JSON)
        """
        room = f"role:{role.lower()}"
        await self._emit_to_room(room, event_type, data)

    async def broadcast_to_order(self, order_id: int, event_type: str, data: dict[str, Any]) -> None:
        """
        Envía un evento a todos los sockets suscritos a un pedido específico.

        Ejemplo:
          broadcast_to_order(5, "PEDIDO_EN_PREPARACION", pedido_data)
          → el cliente que hizo el pedido #5 recibe la actualización

        Args:
            order_id:  ID del pedido
            event_type: Tipo de evento
            data:      Datos del pedido
        """
        room = f"order:{order_id}"
        await self._emit_to_room(room, event_type, data)

    async def broadcast_to_roles(
        self, roles: list[str], event_type: str, data: dict[str, Any]
    ) -> None:
        """
        Envía un evento a múltiples rooms de rol SIN duplicar envíos.

        Si un socket está en varias rooms (ej: admin en role:admin Y role:pedidos),
        solo recibe el evento una vez. Esto evita que un admin vea duplicados.

        Ejemplo:
          broadcast_to_roles(["pedidos", "cocina"], "PEDIDO_CONFIRMADO", data)
          → cajeros y cocineros reciben el evento, pero nadie lo recibe dos veces

        Args:
            roles:      Lista de nombres de rol (ej: ["pedidos", "cocina"])
            event_type: Tipo de evento
            data:      Datos del pedido
        """
        sent_to: set[WebSocket] = set()
        payload = {"event": event_type, "data": data}

        for role in roles:
            room = f"role:{role.lower()}"
            if room not in self.rooms:
                continue
            for connection in list(self.rooms[room]):
                if connection not in sent_to:
                    try:
                        await connection.send_json(payload)
                        sent_to.add(connection)
                    except Exception as e:
                        # Conexión caída — la removemos y seguimos con las demás
                        logger.warning(f"Error al enviar WebSocket. Removiendo conexión: {e}")
                        self.disconnect(connection)

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        """
        Broadcast a TODAS las conexiones activas (método de fallback).

        Este método existe por compatibilidad y para casos donde se necesita
        notificar a todos sin importar el rol. En el uso normal del sistema,
        se prefieren broadcast_to_role() y broadcast_to_order().

        Evita duplicados: si un socket está en múltiples rooms, solo recibe
        el evento una vez.
        """
        sent_to: set[WebSocket] = set()
        payload = {"event": event_type, "data": data}

        for room_connections in self.rooms.values():
            for connection in list(room_connections):
                if connection not in sent_to:
                    try:
                        await connection.send_json(payload)
                        sent_to.add(connection)
                    except Exception as e:
                        logger.warning(f"Error al enviar WebSocket. Removiendo conexión: {e}")
                        self.disconnect(connection)

    # =========================================================================
    # UTILIDADES DE DEBUG
    # =========================================================================

    def get_active_connections_count(self) -> int:
        """
        Retorna el total de conexiones únicas activas.

        Útil para monitoreo y health checks.
        """
        return len(self.socket_rooms)

    def get_rooms_info(self) -> dict[str, int]:
        """
        Retorna información de debug: cada room y cuántos sockets tiene.

        Ejemplo de retorno:
          {
            "role:cocina": 2,
            "role:pedidos": 1,
            "order:5": 1,
          }

        Útil para endpoints de debug o monitoreo.
        """
        return {room: len(sockets) for room, sockets in self.rooms.items()}

    # =========================================================================
    # MÉTODOS PRIVADOS
    # =========================================================================

    def _join_room(self, websocket: WebSocket, room: str) -> None:
        """
        Método interno para agregar un socket a una room.

        Actualiza AMBOS mapos de datos:
          1. self.rooms[room].add(websocket)         — la room sabe que el socket está ahí
          2. self.socket_rooms[websocket].add(room)   — el socket sabe en qué rooms está

        Esta duplicación de estado es intencional: permite consultas eficientes
        en ambas direcciones (¿quién está en esta room? / ¿en qué rooms está este socket?).

        Args:
            websocket: La conexión a agregar
            room:      Nombre de la room (ej: "role:cocina", "order:5")
        """
        # Agregar socket a la room
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(websocket)

        # Agregar room al socket (mapa inverso)
        if websocket not in self.socket_rooms:
            self.socket_rooms[websocket] = set()
        self.socket_rooms[websocket].add(room)

    async def _emit_to_room(self, room: str, event_type: str, data: dict[str, Any]) -> None:
        """
        Método interno para enviar un evento a todos los sockets de una room.

        Si la room no existe o está vacía, el evento se descarta silenciosamente
        (no es un error — simplemente no hay nadie escuchando).

        Si un socket falla al recibir el evento (conexión caída), se remueve
        de todas las rooms y se continúa con los demás.

        Args:
            room:       Nombre de la room destino
            event_type: Tipo de evento (ej: "PEDIDO_CONFIRMADO")
            data:      Datos a enviar (se serializa a JSON automáticamente)
        """
        if room not in self.rooms:
            logger.info(f"Evento {event_type} descartado (room {room} vacía).")
            return

        payload = {"event": event_type, "data": data}
        logger.info(f"Emit {event_type} a room {room} ({len(self.rooms[room])} sockets).")

        for connection in list(self.rooms[room]):
            try:
                await connection.send_json(payload)
            except Exception as e:
                # Conexión caída — la removemos y seguimos con las demás
                logger.warning(f"Error al enviar WebSocket. Removiendo conexión: {e}")
                self.disconnect(connection)


# =============================================================================
# INSTANCIA GLOBAL (SINGLETON)
# =============================================================================
# El ConnectionManager es un singleton — una sola instancia para toda la app.
#
# Se importa desde:
#   - router.py:   para connect() y disconnect() en el handshake/desconexión
#   - service.py:  para broadcast_to_order() y broadcast_to_roles() al cambiar estado
#
# Uso:
#   from app.core.websocket import manager
#   await manager.broadcast_to_role("cocina", "PEDIDO_CONFIRMADO", pedido_data)
#
manager = ConnectionManager()
