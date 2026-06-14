from decimal import Decimal
from sqlmodel import SQLModel


class ResumenResponse(SQLModel):
    ventas_hoy: Decimal
    ticket_promedio: Decimal
    pedidos_activos: int
    ingresos_mes: Decimal


class VentasPeriodoItem(SQLModel):
    periodo: str
    total_ventas: Decimal
    cantidad_pedidos: int


class ProductoTopItem(SQLModel):
    nombre: str
    ingresos: Decimal
    cantidad_vendida: int


class PedidosEstadoItem(SQLModel):
    estado_codigo: str
    cantidad: int


class IngresosResponse(SQLModel):
    forma_pago_codigo: str
    total: Decimal
    cantidad: int
