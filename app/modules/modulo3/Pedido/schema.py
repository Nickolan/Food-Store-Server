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
    

class PedidoRead(PedidoBase):
    id: int
    detalle: List[DetalleRead] = []

class PedidoUpdate(SQLModel):
    estado_codigo: Optional[str] = None
    notas: Optional[str] = None
