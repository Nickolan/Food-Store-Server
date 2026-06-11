import json
from typing import List, Annotated

from sqlmodel import Session   

from app.core.security import decode_access_token
from app.modules.usuario.unit_of_work import UsuarioUnitOfWork
from app.core.database import get_session
from app.core.database import engine
from app.modules.modulo3.HistorialEstadoPedido.schema import HistorialEstadoPedidoRead
from app.modules.modulo3.Pedido.schema import PedidoCreate, PedidoRead, PedidoUpdate
from app.modules.modulo3.Pedido.unitOfWork import PedidoUnitOfWork
from app.modules.modulo3.Pedido.service import PedidoService 
from fastapi import APIRouter, Depends, HTTPException, Path, Query, WebSocket, WebSocketDisconnect, status
from app.core.deps import get_current_user, require_roles
from app.modules.usuario.models import Usuario

router = APIRouter(prefix="/pedidos", tags=["Pedido"])
def get_service(session:Session=Depends(get_session)):
    uow=PedidoUnitOfWork(session)
    return PedidoService(uow=uow)

@router.post(
    "/", 
    response_model=PedidoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(["ADMIN", "CLIENT"]))],
)
async def crear_pedido(current_user: Annotated[Usuario, Depends(get_current_user)], data: PedidoCreate, service: PedidoService = Depends(get_service)):
    return await service.crear(data, current_user.id)

@router.get(
    "/", 
    response_model=List[PedidoRead],
    dependencies=[Depends(require_roles(["ADMIN", "CLIENT", "PEDIDOS"]))],
)
def obtener_pedidos(skip:Annotated[int, Query(ge=0, description="No puede ser negativo")] = 0, limit:Annotated[int, Query(gt=0, le=100, description="Mínimo 1, máximo 100")] = 100, service:PedidoService=Depends(get_service), current_user: Annotated[Usuario, Depends(get_current_user)]=None):
    user_role_codes = [rol.codigo.upper() for rol in current_user.roles]
    if not any(role in ["ADMIN", "PEDIDOS"] for role in user_role_codes):
        return service.obtener_pedidos_por_usuario(current_user.id, skip, limit)
    else:
     return service.obtener_todos(skip,limit)    

@router.get(
    "/{id}", 
    response_model=PedidoRead,
    dependencies=[Depends(require_roles(["ADMIN", "CLIENT", "PEDIDOS"]))],
)
def obtener_pedido_por_id(id: Annotated[int, Path(gt=0, title="ID del pedido", description="Debe ser mayor a 0")],current_user: Annotated[Usuario, Depends(get_current_user)], service:PedidoService=Depends(get_service)):
    pedido=service.obtener_por_id(id)
    user_role_codes = [rol.codigo.upper() for rol in current_user.roles]
    if not any(role in ["ADMIN", "PEDIDOS"] for role in user_role_codes):
        if pedido.usuario_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tenes permiso para acceder a este pedido. Solo podes acceder a tus propios pedidos.")
    return pedido

@router.put("/{id}", response_model=PedidoRead, dependencies=[Depends(require_roles(["ADMIN", "PEDIDOS"]))])
async def actualizar_pedido(id: Annotated[int, Path(gt=0, title="ID del pedido", description="Debe ser mayor a 0")], data: PedidoUpdate, current_user: Annotated[Usuario, Depends(get_current_user)], service: PedidoService = Depends(get_service)):
    user_role_codes = [rol.codigo.upper() for rol in current_user.roles]
    if "ADMIN" in user_role_codes:
        usuario_rol = "ADMIN"
    elif "PEDIDOS" in user_role_codes:
        usuario_rol = "PEDIDOS"
    else:
        usuario_rol = user_role_codes[0] if user_role_codes else None
    return await service.actualizar(id, data, usuario_rol)

@router.get("/{id}/historial", response_model=List[HistorialEstadoPedidoRead])
def obtener_historial_pedido(id: Annotated[int, Path(gt=0, title="ID del pedido", description="Debe ser mayor a 0")],current_user: Annotated[Usuario, Depends(get_current_user)] ,service:PedidoService=Depends(get_service)):
    pedido=service.obtener_por_id(id)
    user_role_codes = [rol.codigo.upper() for rol in current_user.roles]
    if not any(role in ["ADMIN", "PEDIDOS"] for role in user_role_codes):
        if pedido.usuario_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tenes permiso para acceder a este historial. Solo podes acceder al de aquellos pedidos que te pertenezcan.")
    return service.obtener_historial(id)

@router.delete(
    "/{id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(["ADMIN", "PEDIDOS", "CLIENT"]))],
)
async def cancelar_pedido(id: Annotated[int, Path(gt=0, title="ID del pedido", description="Debe ser mayor a 0")], current_user: Annotated[Usuario, Depends(get_current_user)], service: PedidoService = Depends(get_service), motivo: str = Query(..., description="Motivo de cancelación")):
    user_role_codes = [rol.codigo.upper() for rol in current_user.roles]
    if "ADMIN" in user_role_codes:
        usuario_rol = "ADMIN"
    elif "PEDIDOS" in user_role_codes:
        usuario_rol = "PEDIDOS"
    else:
        usuario_rol = user_role_codes[0] if user_role_codes else None
    return await service.cancelar_pedido(id, motivo, current_user.id, usuario_rol)


@router.websocket("/cocina/ws")
async def websocket_endpoint(
    websocket: WebSocket,
):
    token = websocket.cookies.get("access_token")

    if not token:
        await websocket.accept()
        await websocket.close(code=1008, reason="Token de autenticación requerido")
        return

    payload = decode_access_token(token)
    if not payload:
        await websocket.accept()
        await websocket.close(code=1008, reason="Token inválido o expirado")
        return

    username = payload.get("sub")
    if not username:
        await websocket.accept()
        await websocket.close(code=1008, reason="Token inválido")
        return

    with Session(engine) as db_session:
        with UsuarioUnitOfWork(db_session) as uow:
            user = uow.usuarios.get_by_username(username)
            if not user or user.disabled:
                await websocket.accept()
                await websocket.close(code=1008, reason="Usuario inválido o inactivo")
                return
            user_roles = [rol.codigo.lower() for rol in user.roles]
            user_role = user_roles[0] if user_roles else "user"
            user_id: int = user.id

    from app.core.websocket import manager
    await manager.connect(websocket, role=user_role, user_id=user_id)

    # Si el usuario tiene múltiples roles y uno es ADMIN, lo unimos también a role:admin
    # (connect() ya lo une a su rol primario; esto cubre el caso multi-rol)
    user_roles_upper = [r.upper() for r in user_roles]
    if "ADMIN" in user_roles_upper and "role:admin" not in manager.socket_rooms.get(websocket, set()):
        manager._join_room(websocket, "role:admin")

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            action = msg.get("action")

            if action == "subscribe-order":
                order_id = msg.get("order_id")
                if not order_id or not isinstance(order_id, int):
                    continue

                if rol_upper not in ("ADMIN", "PEDIDOS"):
                    with Session(engine) as db_session:
                        with UsuarioUnitOfWork(db_session) as uow:
                            from app.modules.modulo3.Pedido.unitOfWork import PedidoUnitOfWork
                            pedido_uow = PedidoUnitOfWork(db_session)
                            pedido = pedido_uow.pedidos.get_by_id(order_id)

                            if not pedido or pedido.usuario_id != user_id:
                                await websocket.send_json({
                                    "event": "ERROR",
                                    "data": {"detail": "No autorizado para este pedido"}
                                })
                                continue

                manager.join_order_room(websocket, order_id)

                await websocket.send_json({
                    "event": "SUBSCRIBED",
                    "data": {"order_id": order_id}
                })

            elif action == "unsubscribe-order":
                order_id = msg.get("order_id")
                if order_id and isinstance(order_id, int):
                    manager.leave_order_room(websocket, order_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
