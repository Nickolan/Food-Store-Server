from typing import List, Optional

from pydantic import Field

from sqlmodel import SQLModel

from datetime import datetime



# ─── Base ──────────────────────────────────────────────────────────────────

class IngredienteBase(SQLModel):

    nombre: str = Field(..., min_length=3, examples=["Harina"])

    descripcion: str = Field(..., min_length=3, examples=["Harina de trigo para repostería"])

    es_alergeno: bool = Field(default=False, nullable=True)

    activo: bool = Field(default=True, nullable=False)

# ─── Request schemas ───────────────────────────────────────────────────────

class IngredienteCreate(IngredienteBase):

    pass



class IngredienteUpdate(SQLModel):

    nombre: Optional[str] = Field(None, min_length=3)

    descripcion: Optional[str] = Field(None, min_length=3)

    es_alergeno: Optional[bool] = None

    activo: bool = Field(default=True, nullable=False)



# ─── Response schemas ──────────────────────────────────────────────────────

class IngredienteRead(IngredienteBase):

    id: int

    # created_at: datetime

    # updated_at: datetime



class IngredientePaginadoResponse(SQLModel):

    total: int

    items: List[IngredienteRead]



# ─── Operaciones N:M ──────────────────────────────────────────────────────

class ProductoBasicRead(SQLModel):

    """Schema reducido para evitar import circular."""

    id: int

    nombre: str

    precio_base: float



class IngredienteProductoAssign(SQLModel):

    producto_id: int

    es_removible: bool = Field(default=True)



class IngredienteReadFull(IngredienteRead):

    productos: List[ProductoBasicRead] = []