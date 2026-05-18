from .model import FormaPagoBase
from typing import Optional
from pydantic import Field
from sqlmodel import SQLModel

class FormaPagoCreate(FormaPagoBase):
    pass
class FormaPagoRead(FormaPagoBase):
    pass
class FormaPagoUpdate(SQLModel):
    descripcion: Optional[str] = None
    habilitado: Optional[bool] = None