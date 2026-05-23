from typing import List, Annotated

from sqlmodel import Session   

from app.core.database import get_session
from app.modules.modulo3.HistorialEstadoPedido.schema import HistorialEstadoPedidoRead
from app.modules.modulo3.Pedido.schema import PedidoCreate, PedidoRead, PedidoUpdate
from app.modules.modulo3.Pedido.unitOfWork import PedidoUnitOfWork
from app.modules.modulo3.Pedido.service import PedidoService 
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from app.core.deps import get_current_user, require_roles
from app.modules.usuario.models import Usuario

router = APIRouter(prefix="/pedidos", tags=["Pedido"])
def get_service(session:Session=Depends(get_session)):
    uow=PedidoUnitOfWork(session)
    return PedidoService(uow=uow)

@router.post(
    "/", 
    response_model=PedidoRead,
    dependencies=[Depends(require_roles(["ADMIN", "CLIENT"]))],
)
def crear_pedido(current_user: Annotated[Usuario, Depends(get_current_user)],data:PedidoCreate, service:PedidoService=Depends(get_service)):
    return service.crear(data, current_user.id)

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
def actualizar_pedido(id: Annotated[int, Path(gt=0, title="ID del pedido", description="Debe ser mayor a 0")], data:PedidoUpdate, current_user: Annotated[Usuario, Depends(get_current_user)], service:PedidoService=Depends(get_service)):
    user_role_codes = [rol.codigo.upper() for rol in current_user.roles]
    usuario_rol = "ADMIN" if "ADMIN" in user_role_codes else (user_role_codes[0] if user_role_codes else None)
    return service.actualizar(id,data,usuario_rol)

@router.get("/{id}/historial", response_model=List[HistorialEstadoPedidoRead])
def obtener_historial_pedido(id: Annotated[int, Path(gt=0, title="ID del pedido", description="Debe ser mayor a 0")],current_user: Annotated[Usuario, Depends(get_current_user)] ,service:PedidoService=Depends(get_service)):
    pedido=service.obtener_por_id(id)
    user_role_codes = [rol.codigo.upper() for rol in current_user.roles]
    if not any(role in ["ADMIN", "PEDIDOS"] for role in user_role_codes):
        if pedido.usuario_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tenes permiso para acceder a este historial. Solo podes acceder al tuyo.")
    return service.obtener_historial(id)

@router.delete(
    "/{id}", 
    response_model=PedidoRead, 
    dependencies=[Depends(require_roles(["ADMIN", "PEDIDOS"]))],
)
def eliminar_pedido(id: Annotated[int, Path(gt=0, title="ID del pedido", description="Debe ser mayor a 0")], current_user: Annotated[Usuario, Depends(get_current_user)], service:PedidoService=Depends(get_service)):
    return service.borrado_logico(id)
