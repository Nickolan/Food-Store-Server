from typing import List, Optional

from pydantic import Field

from sqlmodel import SQLModel

from datetime import datetime

from app.modules.unidad_medida.schemas import UnidadMedidaRead



# ─── Base ──────────────────────────────────────────────────────────────────

class IngredienteBase(SQLModel):

    nombre: str = Field(..., min_length=3, examples=["Harina"])

    descripcion: str = Field(default="", min_length=0, examples=["Harina de trigo para repostería"])

    stock_cantidad: int = Field(default=0, ge=0, examples=[100])

    precio: float = Field(default=0.0, ge=0, examples=[25.50])

    es_alergeno: bool = Field(default=False)

    activo: bool = Field(default=True)

    unidad_medida_id: Optional[int] = Field(default=None)

# ─── Request schemas ───────────────────────────────────────────────────────

class IngredienteCreate(IngredienteBase):

    pass



class IngredienteUpdate(SQLModel):

    nombre: Optional[str] = Field(None, min_length=3)

    descripcion: Optional[str] = Field(None, min_length=0)

    stock_cantidad: Optional[int] = Field(None, ge=0)

    precio: Optional[float] = Field(None, ge=0)

    es_alergeno: Optional[bool] = None

    activo: Optional[bool] = None

    unidad_medida_id: Optional[int] = None



# ─── Response schemas ──────────────────────────────────────────────────────

class IngredienteRead(IngredienteBase):

    id: int

    unidad_medida: Optional[UnidadMedidaRead] = None

    # created_at: datetime

    # updated_at: datetime



class IngredientePaginadoResponse(SQLModel):

    total: int

    items: List[IngredienteRead]



# ─── Operaciones N:M ──────────────────────────────────────────────────────
class IngredienteBasicRead(SQLModel):
    id: int
    nombre: str
    stock_cantidad: int
    es_alergeno: bool
    activo: bool
    
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