from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlmodel import Session
from app.core.database import get_session
from app.core.deps import get_current_active_user
from app.modules.usuario.models import Usuario
from app.modules.direccionEntrega.schemas import DireccionCreate, DireccionUpdate, DireccionRead, DireccionPaginadoResponse
from app.modules.direccionEntrega.services import DireccionService

router = APIRouter(prefix="/direcciones", tags=["Direcciones"])

def get_direccion_service(session: Session = Depends(get_session)) -> DireccionService:
    return DireccionService(session)

@router.post("/", response_model=DireccionRead, status_code=status.HTTP_201_CREATED)
def crear_direccion(
    direccion_data: DireccionCreate,
    current_user: Usuario = Depends(get_current_active_user),
    svc: DireccionService = Depends(get_direccion_service)
) -> DireccionRead:
    return svc.crear(current_user.id, direccion_data)

@router.get("/", response_model=List[DireccionRead], status_code=status.HTTP_200_OK)
def listar_mis_direcciones(
    current_user: Usuario = Depends(get_current_active_user),
    svc: DireccionService = Depends(get_direccion_service)
) -> List[DireccionRead]:
    return svc.listar_por_usuario(current_user.id)

@router.get("/{direccion_id}", response_model=DireccionRead, status_code=status.HTTP_200_OK)
def detalle_direccion(
    direccion_id: int = Path(..., gt=0),
    current_user: Usuario = Depends(get_current_active_user),
    svc: DireccionService = Depends(get_direccion_service)
) -> DireccionRead:
    return svc.obtener_por_id(current_user.id, direccion_id)

@router.put("/{direccion_id}", response_model=DireccionRead, status_code=status.HTTP_200_OK)
def actualizar_direccion(
    direccion_data: DireccionUpdate,
    direccion_id: int = Path(..., gt=0),
    current_user: Usuario = Depends(get_current_active_user),
    svc: DireccionService = Depends(get_direccion_service)
) -> DireccionRead:
    return svc.actualizar(current_user.id, direccion_id, direccion_data)

@router.delete("/{direccion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_direccion(
    direccion_id: int = Path(..., gt=0),
    current_user: Usuario = Depends(get_current_active_user),
    svc: DireccionService = Depends(get_direccion_service)
):
    svc.eliminar(current_user.id, direccion_id)
    return None