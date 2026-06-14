from datetime import date
from typing import List, Literal

from .repository import EstadisticasRepository
from .schemas import (
    IngresosResponse,
    PedidosEstadoItem,
    ProductoTopItem,
    ResumenResponse,
    VentasPeriodoItem,
)

_AGRUPACIONES_VALIDAS = frozenset({"day", "week", "month"})


class EstadisticasService:
    def __init__(self, repo: EstadisticasRepository) -> None:
        self.repo = repo

    def get_resumen(self) -> ResumenResponse:
        return self.repo.get_resumen_kpis()

    def get_ventas(
        self,
        desde: date,
        hasta: date,
        agrupacion: str = "day",
    ) -> List[VentasPeriodoItem]:
        if agrupacion not in _AGRUPACIONES_VALIDAS:
            raise ValueError(
                f"agrupacion inválida: '{agrupacion}'. "
                f"Valores permitidos: {sorted(_AGRUPACIONES_VALIDAS)}"
            )
        return self.repo.get_ventas_periodo(desde, hasta, agrupacion)

    def get_productos_top(self, limit: int = 10) -> List[ProductoTopItem]:
        return self.repo.get_productos_top(limit)

    def get_pedidos_por_estado(self) -> List[PedidosEstadoItem]:
        return self.repo.get_pedidos_por_estado()

    def get_ingresos(self, desde: date, hasta: date) -> List[IngresosResponse]:
        return self.repo.get_ingresos_por_forma_pago(desde, hasta)
