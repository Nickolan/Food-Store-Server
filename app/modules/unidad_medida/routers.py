from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session
from app.core.database import get_session
from app.core.deps import require_roles
from app.modules.unidad_medida.schemas import (
    UnidadMedidaRead,
    UnidadMedidaPaginadoResponse
)
from app.modules.unidad_medida.services import UnidadMedidaService

router = APIRouter(prefix="/api/v6/unidades-medida", tags=["Unidad Medida"])

def get_service(session: Session = Depends(get_session)) -> UnidadMedidaService:
    return UnidadMedidaService(session)

@router.get("/", response_model=UnidadMedidaPaginadoResponse, dependencies=[Depends(require_roles(["ADMIN"]))],)
def listar_unidades(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: UnidadMedidaService = Depends(get_service),
):
    return service.obtener_todas(offset=offset, limit=limit)

@router.get("/{id}", response_model=UnidadMedidaRead, dependencies=[Depends(require_roles(["ADMIN"]))],)
def obtener_unidad(
    id: int,
    service: UnidadMedidaService = Depends(get_service),
):
    return service.obtener_por_id(id)

