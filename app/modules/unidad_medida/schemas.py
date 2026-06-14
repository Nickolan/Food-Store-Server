from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class UnidadMedidaBase(BaseModel):
    nombre: str
    simbolo: str
    tipo: str

class UnidadMedidaCreate(UnidadMedidaBase):
    pass

class UnidadMedidaUpdate(BaseModel):
    nombre: Optional[str] = None
    simbolo: Optional[str] = None
    tipo: Optional[str] = None

class UnidadMedidaRead(UnidadMedidaBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UnidadMedidaPaginadoResponse(BaseModel):
    total: int
    items: List[UnidadMedidaRead]
