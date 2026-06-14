from datetime import date
from typing import Annotated, List

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.database import get_session
from app.core.deps import require_roles
from .repository import EstadisticasRepository
from .schemas import (
    IngresosResponse,
    PedidosEstadoItem,
    ProductoTopItem,
    ResumenResponse,
    VentasPeriodoItem,
)
from .service import EstadisticasService

router = APIRouter(
    prefix="/api/v6/estadisticas",
    tags=["Estadísticas"],
    dependencies=[Depends(require_roles(["ADMIN"]))],
)


def get_service(session: Session = Depends(get_session)) -> EstadisticasService:
    return EstadisticasService(repo=EstadisticasRepository(session))


@router.get("/resumen", response_model=ResumenResponse)
def resumen(service: EstadisticasService = Depends(get_service)):
    return service.get_resumen()


@router.get("/ventas", response_model=List[VentasPeriodoItem])
def ventas_periodo(
    desde: Annotated[date, Query(description="Fecha de inicio (YYYY-MM-DD)")],
    hasta: Annotated[date, Query(description="Fecha de fin (YYYY-MM-DD)")],
    agrupacion: Annotated[str, Query(description="day | week | month")] = "day",
    service: EstadisticasService = Depends(get_service),
):
    return service.get_ventas(desde, hasta, agrupacion)


@router.get("/productos-top", response_model=List[ProductoTopItem])
def productos_top(
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    service: EstadisticasService = Depends(get_service),
):
    return service.get_productos_top(limit)


@router.get("/pedidos-por-estado", response_model=List[PedidosEstadoItem])
def pedidos_por_estado(service: EstadisticasService = Depends(get_service)):
    return service.get_pedidos_por_estado()


@router.get("/ingresos", response_model=List[IngresosResponse])
def ingresos_por_forma_pago(
    desde: Annotated[date, Query(description="Fecha de inicio (YYYY-MM-DD)")],
    hasta: Annotated[date, Query(description="Fecha de fin (YYYY-MM-DD)")],
    service: EstadisticasService = Depends(get_service),
):
    return service.get_ingresos(desde, hasta)
