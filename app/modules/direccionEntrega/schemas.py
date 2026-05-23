from datetime import datetime
from typing import Optional, List
from pydantic import Field
from sqlmodel import SQLModel
from decimal import Decimal

# ─── Base ──────────────────────────────────────────────────────────────────

class DireccionBase(SQLModel):
    alias: Optional[str] = Field(max_length=50, default=None, examples=["Casa", "Oficina"])
    linea1: str = Field(max_length=255, nullable=False, examples=["Av. Siempre Viva 123"])
    linea2: Optional[str] = Field(max_length=255, default=None, examples=["Depto 4B"])
    ciudad: str = Field(max_length=100, nullable=False, examples=["Springfield"])
    provincia: Optional[str] = Field(max_length=10, default=None, examples=["BSAS"])
    codigo_postal: Optional[str] = Field(max_length=10, default=None, examples=["1234"])
    latitud: Optional[Decimal] = Field(max_digits=9, decimal_places=6, default=None, examples=["-34.603722"])
    longitud: Optional[Decimal] = Field(max_digits=9, decimal_places=6, default=None, examples=["-58.381592"])
    es_principal: bool = Field(default=False, nullable=False)

# ─── Request schemas ───────────────────────────────────────────────────────

class DireccionCreate(DireccionBase):
    pass

class DireccionUpdate(SQLModel):
    alias: Optional[str] = Field(None, max_length=50)
    linea1: Optional[str] = Field(None, max_length=255)
    linea2: Optional[str] = Field(None, max_length=255)
    ciudad: Optional[str] = Field(None, max_length=100)
    provincia: Optional[str] = Field(None, max_length=10)
    codigo_postal: Optional[str] = Field(None, max_length=10)
    latitud: Optional[Decimal] = Field(None, max_digits=9, decimal_places=6)
    longitud: Optional[Decimal] = Field(None, max_digits=9, decimal_places=6)
    es_principal: Optional[bool] = None

# ─── Response schemas ──────────────────────────────────────────────────────

class DireccionRead(DireccionBase):
    id: int
    usuario_id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

class DireccionPaginadoResponse(SQLModel):
    total: int
    items: List[DireccionRead]