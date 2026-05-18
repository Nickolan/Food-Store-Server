from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class DireccionBase(BaseModel):
    calle: str = Field(..., min_length=1, max_length=255)
    numero: int = Field(..., gt=0)
    ciudad: str = Field(..., min_length=1, max_length=100)
    codigo_postal: str = Field(..., min_length=1, max_length=20)
    es_principal: bool = False

class DireccionCreate(DireccionBase):
    pass

class DireccionUpdate(BaseModel):
    calle: Optional[str] = Field(None, min_length=1, max_length=255)
    numero: Optional[int] = Field(None, gt=0)
    ciudad: Optional[str] = Field(None, min_length=1, max_length=100)
    codigo_postal: Optional[str] = Field(None, min_length=1, max_length=20)
    es_principal: Optional[bool] = None

class DireccionRead(DireccionBase):
    id: int
    usuario_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True