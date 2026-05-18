from typing import Optional

from pydantic import Field
from sqlmodel import SQLModel

from .model import EstadoPedidoBase


class EstadoPedidoCreate(EstadoPedidoBase):
    pass
class EstadoPedidoRead(EstadoPedidoBase):
    pass
class EstadoPedidoUpdate(SQLModel):
    descripcion:Optional[str] = Field(max_length=80)
    orden:Optional[int] = None
    es_terminal:Optional[bool] = None