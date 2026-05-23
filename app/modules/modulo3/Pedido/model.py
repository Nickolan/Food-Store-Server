from datetime import datetime
from sqlalchemy import Column, Integer
from decimal import Decimal
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.dialects.postgresql import ARRAY

# from app.modules.modulo3.Pago.model import Pago POR AHORA NO SE USA

class PedidoBase(SQLModel):
    direccion_id: Optional[int] = Field(default=None, foreign_key="direccion.id", nullable=True)
    forma_pago_codigo: str = Field(foreign_key="formapago.codigo")
    descuento: Decimal = Field(default=0.00, max_digits=10, decimal_places=2)
    costo_envio: Decimal = Field(default=50.00, max_digits=10, decimal_places=2)

    notas: Optional[str] = Field(default=None)
class DetallePedido(SQLModel, table=True):
    pedido_id: int = Field(primary_key=True, foreign_key="pedido.id", ondelete="CASCADE")
    producto_id: int = Field(primary_key=True, foreign_key="producto.id", ondelete="RESTRICT")
    cantidad: int = Field(default=1, ge=1)
    
    pedido: Optional["Pedido"] = Relationship(back_populates="detalle")

    nombre_snapshot: str = Field(max_length=200, nullable=False)
    precio_snapshot: Decimal = Field(max_digits=10, decimal_places=2, nullable=False, ge=0)
    subtotal_snap: Decimal = Field(max_digits=10, decimal_places=2, nullable=False)
    personalizacion:Optional[list[int]]=Field(default=None, sa_column=Column(ARRAY(Integer)))
 
    created_at: datetime = Field(default_factory=datetime.now)
class Pedido(PedidoBase,table=True):
  id: Optional[int] = Field(default=None, primary_key=True)
  usuario_id:int=Field(nullable=False, foreign_key="usuario.id")
  estado_codigo: str = Field(foreign_key="estadopedido.codigo")
  subtotal: Decimal = Field(default=0, max_digits=10, decimal_places=2)
  total: Decimal = Field(default=0, max_digits=10, decimal_places=2)
  created_at: datetime = Field(default_factory=datetime.now)
  updated_at: datetime = Field(default_factory=datetime.now)
  deleted_at: Optional[datetime] = Field(default=None)

  detalle: List["DetallePedido"] = Relationship(back_populates="pedido")
  # pagos: List["Pago"] = Relationship(back_populates="pedido")
