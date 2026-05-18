from typing import List, Annotated   

from app.modules.modulo3.Pago.schema import PagoCreate, PagoRead, PagoUpdate
from app.modules.modulo3.Pago.unitOfWork import PagoUnitOfWork
from app.modules.modulo3.Pago.service import PagoService 
from fastapi import APIRouter, Depends, Path, Query


router = APIRouter(prefix="/pagos", tags=["Pago"])
def get_service():
    uow=PagoUnitOfWork()
    return PagoService(uow=uow)

@router.post("/", response_model=PagoRead)
def crear_pago(data:PagoCreate, service:PagoService=Depends(get_service)):
    return service.crear(data)

@router.get("/", response_model=List[PagoRead])
def obtener_pagos(skip:Annotated[int, Query(ge=0, description="No puede ser negativo")] = 0, limit:Annotated[int, Query(gt=0, le=100, description="Mínimo 1, máximo 100")] = 100, service:PagoService=Depends(get_service)):
    return service.obtener_todos(skip,limit)    

@router.get("/{id}", response_model=PagoRead)
def obtener_pago_por_id(id: Annotated[int, Path(gt=0, title="ID del pago", description="Debe ser mayor a 0")], service:PagoService=Depends(get_service)):
    return service.obtener_por_id(id)

@router.put("/{id}", response_model=PagoRead)
def actualizar_pago(id: Annotated[int, Path(gt=0, title="ID del pago", description="Debe ser mayor a 0")], data:PagoUpdate, service:PagoService=Depends(get_service)):
    return service.actualizar(id,data)

