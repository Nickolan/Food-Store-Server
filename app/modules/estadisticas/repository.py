from datetime import date
from decimal import Decimal
from typing import List, Literal

from sqlalchemy import Date, cast, func
from sqlmodel import Session, select

from app.modules.modulo3.Pago.model import Pago
from app.modules.modulo3.Pedido.model import DetallePedido, Pedido
from .schemas import (
    IngresosResponse,
    PedidosEstadoItem,
    ProductoTopItem,
    ResumenResponse,
    VentasPeriodoItem,
)

_CANCELADO = "CANCELADO"
_APROBADO = "approved"
_ESTADOS_INACTIVOS = ("CANCELADO", "ENTREGADO")

_TRUNC_FORMAT: dict[str, str] = {
    "day":   "YYYY-MM-DD",
    "week":  "IYYY-IW",
    "month": "YYYY-MM",
}


class EstadisticasRepository:
    def __init__(self, session: Session) -> None:
        self.session = session


    def get_resumen_kpis(self) -> ResumenResponse:
        hoy = date.today()

        ventas_hoy = self.session.scalar(
            select(func.coalesce(func.sum(Pedido.total), Decimal("0")))
            .where(
                cast(Pedido.created_at, Date) == hoy,
                Pedido.estado_codigo != _CANCELADO,
            )
        ) or Decimal("0")

        ticket_promedio = self.session.scalar(
            select(func.coalesce(func.avg(Pedido.total), Decimal("0")))
            .where(Pedido.estado_codigo != _CANCELADO)
        ) or Decimal("0")

        pedidos_activos = self.session.scalar(
            select(func.count(Pedido.id))
            .where(~Pedido.estado_codigo.in_(list(_ESTADOS_INACTIVOS)))
        ) or 0

        ingresos_mes = self.session.scalar(
            select(func.coalesce(func.sum(Pedido.total), Decimal("0")))
            .where(
                func.extract("month", Pedido.created_at) == hoy.month,
                func.extract("year",  Pedido.created_at) == hoy.year,
                Pedido.estado_codigo != _CANCELADO,
            )
        ) or Decimal("0")

        return ResumenResponse(
            ventas_hoy=Decimal(str(ventas_hoy)),
            ticket_promedio=Decimal(str(ticket_promedio)),
            pedidos_activos=int(pedidos_activos),
            ingresos_mes=Decimal(str(ingresos_mes)),
        )


    def get_ventas_periodo(
        self,
        desde: date,
        hasta: date,
        agrupacion: Literal["day", "week", "month"] = "day",
    ) -> List[VentasPeriodoItem]:
        truncated = func.date_trunc(agrupacion, Pedido.created_at)
        periodo_col = func.to_char(truncated, _TRUNC_FORMAT[agrupacion])

        stmt = (
            select(
                periodo_col.label("periodo"),
                func.sum(Pedido.total).label("total_ventas"),
                func.count(Pedido.id).label("cantidad_pedidos"),
            )
            .where(
                cast(Pedido.created_at, Date) >= desde,
                cast(Pedido.created_at, Date) <= hasta,
                Pedido.estado_codigo != _CANCELADO,
            )
            .group_by(truncated)
            .order_by(truncated)
        )
        rows = self.session.execute(stmt).all()
        return [
            VentasPeriodoItem(
                periodo=r.periodo,
                total_ventas=Decimal(str(r.total_ventas)),
                cantidad_pedidos=int(r.cantidad_pedidos),
            )
            for r in rows
        ]


    def get_productos_top(self, limit: int = 10) -> List[ProductoTopItem]:
        stmt = (
            select(
                DetallePedido.nombre_snapshot,
                func.sum(DetallePedido.subtotal_snap).label("ingresos"),
                func.sum(DetallePedido.cantidad).label("cantidad_vendida"),
            )
            .select_from(DetallePedido)
            .join(Pedido, Pedido.id == DetallePedido.pedido_id)
            .where(Pedido.estado_codigo != _CANCELADO)
            .group_by(DetallePedido.producto_id, DetallePedido.nombre_snapshot)
            .order_by(func.sum(DetallePedido.subtotal_snap).desc())
            .limit(limit)
        )
        rows = self.session.execute(stmt).all()
        return [
            ProductoTopItem(
                nombre=r.nombre_snapshot,
                ingresos=Decimal(str(r.ingresos)),
                cantidad_vendida=int(r.cantidad_vendida),
            )
            for r in rows
        ]


    def get_pedidos_por_estado(self) -> List[PedidosEstadoItem]:
        stmt = (
            select(
                Pedido.estado_codigo,
                func.count(Pedido.id).label("cantidad"),
            )
            .group_by(Pedido.estado_codigo)
        )
        rows = self.session.execute(stmt).all()
        return [
            PedidosEstadoItem(estado_codigo=r.estado_codigo, cantidad=int(r.cantidad))
            for r in rows
        ]


    def get_ingresos_por_forma_pago(
        self, desde: date, hasta: date
    ) -> List[IngresosResponse]:
        stmt = (
            select(
                Pedido.forma_pago_codigo,
                func.sum(Pago.transaction_amount).label("total"),
                func.count(Pago.id).label("cantidad"),
            )
            .select_from(Pedido)
            .join(Pago, Pago.pedido_id == Pedido.id)
            .where(
                Pago.mp_status == _APROBADO,
                cast(Pedido.created_at, Date) >= desde,
                cast(Pedido.created_at, Date) <= hasta,
            )
            .group_by(Pedido.forma_pago_codigo)
        )
        rows = self.session.execute(stmt).all()
        return [
            IngresosResponse(
                forma_pago_codigo=r.forma_pago_codigo,
                total=Decimal(str(r.total)),
                cantidad=int(r.cantidad),
            )
            for r in rows
        ]
