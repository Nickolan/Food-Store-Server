from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.core.database import get_session
from app.core.deps import get_current_active_user
from app.modules.usuario.models import Usuario
from app.modules.direccion.schemas import DireccionCreate, DireccionUpdate, DireccionRead
from app.modules.direccion.services import DireccionService
from app.modules.direccion.unit_of_work import DireccionUoW

router = APIRouter(
    prefix="/direcciones",
    tags=["direcciones"]
)

def get_direccion_service(session: Session = Depends(get_session)) -> DireccionService:
    uow = DireccionUoW(session)
    return DireccionService(uow)

@router.post("", response_model=DireccionRead, status_code=status.HTTP_201_CREATED)
async def create_direccion(
    direccion_data: DireccionCreate,
    current_user: Usuario = Depends(get_current_active_user),
    service: DireccionService = Depends(get_direccion_service)
):
    return service.create_direccion(current_user.id, direccion_data)

@router.get("", response_model=List[DireccionRead])
async def get_mis_direcciones(
    current_user: Usuario = Depends(get_current_active_user),
    service: DireccionService = Depends(get_direccion_service)
):
    return service.get_direcciones_by_usuario(current_user.id)

@router.get("/{direccion_id}", response_model=DireccionRead)
async def get_direccion_by_id(
    direccion_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    service: DireccionService = Depends(get_direccion_service)
):
    return service.get_direccion_by_id(direccion_id, current_user.id)

@router.put("/{direccion_id}", response_model=DireccionRead)
async def update_direccion(
    direccion_id: int,
    update_data: DireccionUpdate,
    current_user: Usuario = Depends(get_current_active_user),
    service: DireccionService = Depends(get_direccion_service)
):
    return service.update_direccion(direccion_id, current_user.id, update_data)

@router.delete("/{direccion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_direccion(
    direccion_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    service: DireccionService = Depends(get_direccion_service)
):
    service.delete_direccion(direccion_id, current_user.id)
    return None