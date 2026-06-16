
import logging
from typing import Any
from fastapi import WebSocket

# Logger del módulo para trazabilidad de eventos WebSocket
logger = logging.getLogger("app.core.websocket")


class ConnectionManager:
    

    def __init__(self) -> None:
        
        self.rooms: dict[str, set[WebSocket]] = {}

        self.socket_rooms: dict[WebSocket, set[str]] = {}


    async def connect(self, websocket: WebSocket, role: str, user_id: int) -> None:
        
        await websocket.accept()

        # Normalizar rol a minúsculas para consistencia en nombres de room
        # "PEDIDOS" → "role:pedidos", "Admin" → "role:admin"
        role_key = f"role:{role.lower()}"

        # Unir el socket a su room de rol
        self._join_room(websocket, role_key)

        logger.info(
            f"Conexión WebSocket aceptada. user_id={user_id}, role={role}, "
            f"room={role_key}. Total rooms activas: {len(self.rooms)}"
        )

    def disconnect(self, websocket: WebSocket) -> None:
        
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
        
        room = f"order:{order_id}"
        self._join_room(websocket, room)
        logger.info(f"Socket suscrito a room {room}")

    def leave_order_room(self, websocket: WebSocket, order_id: int) -> None:
       
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
       
        room = f"role:{role.lower()}"
        await self._emit_to_room(room, event_type, data)

    async def broadcast_to_order(self, order_id: int, event_type: str, data: dict[str, Any]) -> None:
        room = f"order:{order_id}"
        logger.debug("Emitiendo a room %s: event=%s", room, event_type)
        await self._emit_to_room(room, event_type, data)

    async def broadcast_to_roles(
        self, roles: list[str], event_type: str, data: dict[str, Any]
    ) -> None:
       
        sent_to: set[WebSocket] = set()
        payload = {"event": event_type, "data": data}

        for role in roles:
            room = f"role:{role.lower()}"
            logger.debug("broadcast_to_roles: event=%s, room=%s", event_type, room)
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
        
        return len(self.socket_rooms)

    def get_rooms_info(self) -> dict[str, int]:
       
        return {room: len(sockets) for room, sockets in self.rooms.items()}

    # =========================================================================
    # MÉTODOS PRIVADOS
    # =========================================================================

    def _join_room(self, websocket: WebSocket, room: str) -> None:
        
        # Agregar socket a la room
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(websocket)

        # Agregar room al socket (mapa inverso)
        if websocket not in self.socket_rooms:
            self.socket_rooms[websocket] = set()
        self.socket_rooms[websocket].add(room)

    async def _emit_to_room(self, room: str, event_type: str, data: dict[str, Any]) -> None:
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


manager = ConnectionManager()
