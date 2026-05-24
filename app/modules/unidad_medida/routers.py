from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session
from app.core.database import get_session
from app.core.deps import require_roles
from app.modules.unidad_medida.schemas import (
    UnidadMedidaCreate,
    UnidadMedidaUpdate,
    UnidadMedidaRead,
    UnidadMedidaPaginadoResponse
)
from app.modules.unidad_medida.services import UnidadMedidaService

router = APIRouter(prefix="/unidades-medida", tags=["Unidad Medida"])

def get_service(session: Session = Depends(get_session)) -> UnidadMedidaService:
    return UnidadMedidaService(session)

@router.get("/", response_model=UnidadMedidaPaginadoResponse)
def listar_unidades(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: UnidadMedidaService = Depends(get_service)
):
    return service.obtener_todas(offset=offset, limit=limit)

@router.get("/{id}", response_model=UnidadMedidaRead)
def obtener_unidad(
    id: int,
    service: UnidadMedidaService = Depends(get_service)
):
    return service.obtener_por_id(id)

@router.post("/", response_model=UnidadMedidaRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))])
def crear_unidad(
    data: UnidadMedidaCreate,
    service: UnidadMedidaService = Depends(get_service)
):
    return service.crear(data)

@router.put("/{id}", response_model=UnidadMedidaRead, dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))])
def actualizar_unidad(
    id: int,
    data: UnidadMedidaUpdate,
    service: UnidadMedidaService = Depends(get_service)
):
    return service.actualizar(id, data)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))])
def eliminar_unidad(
    id: int,
    service: UnidadMedidaService = Depends(get_service)
):
    service.eliminar(id)
