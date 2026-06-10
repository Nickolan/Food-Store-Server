from typing import List, Annotated   

from app.modules.modulo3.Pago.schema import PagoCreate, PagoRead, PagoUpdate
from app.modules.modulo3.Pago.unitOfWork import PagoUnitOfWork
from app.modules.modulo3.Pago.service import PagoService 
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status, Request, Response
import hmac
import hashlib
from app.core.config import settings
from app.core.database import get_session
from sqlmodel import Session
from app.core.deps import get_current_user, require_roles
from app.modules.usuario.models import Usuario

router = APIRouter(prefix="/api/v1/pagos", tags=["Pago"])

def get_service(session: Session = Depends(get_session)):
    uow = PagoUnitOfWork(session)
    return PagoService(uow=uow)

@router.post(
    "/", 
    response_model=PagoRead,
    dependencies=[Depends(require_roles(["ADMIN", "CLIENT"]))],
)
def crear_pago(data: PagoCreate, service: PagoService = Depends(get_service)):
    return service.crear(data)

@router.post("/webhook")
async def mp_webhook(request: Request, service: PagoService = Depends(get_service)):
    # Mercado Pago puede mandar los IDs por query params (ej: ?data.id=123) o en el body
    data_id = request.query_params.get("data.id")
    
    if not data_id:
        # Intentar sacarlo del body si no está en la query
        try:
            data = await request.json()
            data_id = data.get("data", {}).get("id")
        except:
            pass

    if data_id:
        # Se procesa el webhook de manera segura (el SDK va y le pregunta a MP si el pago es real)
        service.procesar_webhook(data_id)
        
    return Response(status_code=200)

@router.get(
    "/", 
    response_model=List[PagoRead],
    dependencies=[Depends(require_roles(["ADMIN", "CLIENT"]))],
)
def obtener_pagos(
    current_user: Annotated[Usuario, Depends(get_current_user)],
    skip: Annotated[int, Query(ge=0)] = 0, 
    limit: Annotated[int, Query(gt=0, le=100)] = 100, 
    session: Session = Depends(get_session),
    service: PagoService = Depends(get_service),
):
    if current_user.role.upper() != "ADMIN":
        todos = service.obtener_todos(skip=0, limit=9999)
        uow = PagoUnitOfWork(session)
        pagos_usuario = []
        with uow as u:
            for p in todos:
                if p.pedido_id:
                    pedido = u.pedidos.obtener_por_id(p.pedido_id)
                    if pedido and pedido.usuario_id == current_user.id:
                        pagos_usuario.append(p)
        return pagos_usuario[skip : skip + limit]
        
    return service.obtener_todos(skip, limit)

@router.get(
    "/{id}", 
    response_model=PagoRead,
    dependencies=[Depends(require_roles(["ADMIN", "CLIENT"]))],
)
def obtener_pago_por_id(
    current_user: Annotated[Usuario, Depends(get_current_user)],
    id: Annotated[int, Path(gt=0)], 
    session: Session = Depends(get_session),
    service: PagoService = Depends(get_service),
):
    pago = service.obtener_por_id(id)
    
    if not pago:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado"
        )
        
    if current_user.role.upper() != "ADMIN":
        uow = PagoUnitOfWork(session)
        with uow as u:
            pedido = u.pedidos.obtener_por_id(pago.pedido_id)
            if not pedido or pedido.usuario_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="No tenes permiso para acceder a este pago"
                )
    return pago

@router.put(
    "/{id}", 
    response_model=PagoRead,
    dependencies=[Depends(require_roles(["ADMIN", "PEDIDOS"]))],
)
def actualizar_pago(id: Annotated[int, Path(gt=0)], data: PagoUpdate, service: PagoService = Depends(get_service)):
    return service.actualizar(id, data)