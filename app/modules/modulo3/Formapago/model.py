from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class FormaPagoBase(SQLModel):
    codigo: str = Field(primary_key=True, max_length=20)
    descripcion: str = Field(nullable=False)
    habilitado: bool = Field(nullable=False, default=True)
class FormaPago(FormaPagoBase, table=True):
    pass