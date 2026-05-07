from typing import List, Optional
from pydantic import Field
from sqlmodel import SQLModel
from datetime import datetime

# ─── Base ──────────────────────────────────────────────────────────────────
class CategoriaBase(SQLModel):
    nombre: str = Field(..., index=True, examples=["Bebidas"])
    descripcion: str = Field(..., min_length=3, examples=["Categoría para bebidas frías y calientes."])
    imagen_url: Optional[str] = Field(default=None, nullable=True, examples=["https://example.com/categoria/muebles.jpg"])
    activo: bool = Field(default=True, nullable=False)

# ─── Request schemas ───────────────────────────────────────────────────────
class CategoriaCreate(CategoriaBase):
    pass

class CategoriaUpdate(SQLModel):
    nombre: Optional[str] = Field(None, index=True, examples=["Bebidas"])
    descripcion: Optional[str] = Field(None, min_length=3)
    imagen_url: Optional[str] = Field(default=None, nullable=True, examples=["https://example.com/categoria/muebles.jpg"])
    activo: Optional[bool] = None
    parent_id: Optional[int] = Field(default=None, examples=[1])

# ─── Response schemas ──────────────────────────────────────────────────────
class CategoriaRead(CategoriaBase):
    id: int
    parent_id: Optional[int] = None
    # created_at: datetime
    # updated_at: datetime
    # deleted_at: Optional[datetime] = None

class ProductoBasicRead(SQLModel):
    """Schema reducido para evitar import circular."""
    id: int
    nombre: str
    precio_base: float
    activo: bool
    disponible: bool

class CategoriaReadFull(CategoriaRead):
    """Categoria con sus productos (N:M)."""
    productos: List[ProductoBasicRead] = []
    # categoria: Optional[CategoriaRead] = None
    subcategorias: List[CategoriaRead] = []

class CategoriaPaginadoResponse(SQLModel):
    total: int
    items: List[CategoriaRead]