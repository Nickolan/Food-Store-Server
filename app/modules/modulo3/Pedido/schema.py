from decimal import Decimal
from typing import List, Optional
from pydantic import Field
from datetime import datetime

from sqlmodel import SQLModel
from .model import PedidoBase

class DetalleCreate(SQLModel):
    producto_id: int
    cantidad: int = Field(..., gt=0)
    personalizacion: Optional[list[int]] = None

class PedidoCreate(PedidoBase):
    items: list[DetalleCreate]

class DetalleRead(SQLModel):
    producto_id: int
    cantidad: int
    nombre_snapshot: str
    precio_snapshot: Decimal
    subtotal_snap: Decimal
    personalizacion: Optional[list[int]] = None
    created_at: Optional[datetime] = None

class PedidoRead(PedidoBase):
    id: int
    usuario_id:int
    estado_codigo: str 
    subtotal: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    total: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    detalle: List[DetalleRead] = []

class PedidoUpdate(SQLModel):
    estado_codigo: str
    motivo: Optional[str] = None
