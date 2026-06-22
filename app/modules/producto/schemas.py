from typing import List, Optional
from pydantic import Field
from sqlmodel import SQLModel
from decimal import Decimal
from app.modules.ingrediente.schemas import IngredienteBasicRead
from app.modules.unidad_medida.schemas import UnidadMedidaRead

# ─── Base ──────────────────────────────────────────────────────────────────
class ProductoBase(SQLModel):
    nombre: str = Field(..., examples=["Cerveza Quilmes"])
    descripcion: str = Field(..., examples=["Cerveza rubia, ideal para acompañar una picada."])
    precio_base: float = Field(gt=0, examples=[150.50])
    stock_minimo: int = Field(ge=0, examples=[5])
    imagenes_url: List[str] = Field(default_factory=list, examples=[["https://example.com/producto/pizza.jpg"]])
    disponible: bool = True

# ─── Nuevo schema para ingredientes en creación ───────────────────────────
class ProductoIngredienteCreate(SQLModel):
    """Schema para asociar un ingrediente al crear un producto"""
    ingrediente_id: int
    es_removible: bool = False
    cantidad: Decimal = Field(..., gt=0)

# ─── Request schemas ───────────────────────────────────────────────────────
class ProductoCreate(ProductoBase):
    unidad_venta_id: Optional[int] = None
    ingredientes: Optional[List[ProductoIngredienteCreate]] = Field(default_factory=list, description="Lista de ingredientes con su propiedad removible")
    categorias_ids: Optional[List[int]] = Field(default_factory=list, description="IDs de categorías a las que pertenece el producto")

class ProductoUpdate(SQLModel):
    nombre: Optional[str] = Field(None, examples=["Cerveza Quilmes"])
    descripcion: Optional[str] = Field(None, examples=["Cerveza rubia, ideal para acompañar una picada."])
    precio_base: Optional[float] = Field(None, gt=0)
    stock_minimo: Optional[int] = Field(None, ge=0)
    imagenes_url: Optional[List[str]] = Field(None, examples=[["https://example.com/producto/pizza.jpg"]])
    disponible: Optional[bool] = None
    unidad_venta_id: Optional[int] = None
    ingredientes: Optional[List[ProductoIngredienteCreate]] = Field(None, description="Lista de ingredientes con su propiedad removible")
    categorias_ids: Optional[List[int]] = Field(None, description="IDs de categorías a las que pertenece el producto")

# ─── Response schemas ──────────────────────────────────────────────────────
class ProductoRead(ProductoBase):
    id: int
    activo: bool
    alerta_ingrediente_modificado: bool = False
    unidad_medida: Optional[UnidadMedidaRead] = None

class CategoriaBasicRead(SQLModel):
    """Schema reducido para evitar import circular."""
    id: int
    nombre: str
    descripcion: str
    activo: bool
    imagen_url: Optional[str]
    relacion_principal: Optional[bool] = False

class CategoriaWithPrincipal(SQLModel):
    categoria: CategoriaBasicRead
    es_principal: Optional[bool] = False

class IngredienteWithProductoInfo(SQLModel):
    ingrediente: IngredienteBasicRead
    es_removible: Optional[bool] = None
    cantidad: Optional[Decimal] = None

class ProductoReadFull(ProductoRead):
    """Producto con sus categorías e ingredientes anidados."""
    stock: int = 0
    tiene_alerta_precio: Optional[bool] = None
    categorias: List[CategoriaWithPrincipal] = []
    ingredientes: List[IngredienteWithProductoInfo] = []

# ─── Alertas ────────────────────────────────────────────────────────────────
class ProductoAlertaItem(SQLModel):
    producto_id: int
    nombre: str
    tipo_alerta: str  # "margen_bajo" | "precio_ingrediente_actualizado"
    mensaje: str
    margen_porcentual: float | None = None

class ProductoAlertasResponse(SQLModel):
    total: int
    items: List[ProductoAlertaItem]

class ProductoStockResponse(SQLModel):
    stock: int
    bajo_stock_minimo: bool
    activo: bool
    disponible: bool
    
class ProductoMargenResponse(SQLModel):
    producto_id: int
    precio_venta: float
    costo_total: float
    margen_absoluto: float
    margen_porcentual: float | None = None


# ─── Operaciones N:M ──────────────────────────────────────────────────────
class ProductoCategoriaAssign(SQLModel):
    categoria_id: int
    es_principal: bool = False

class ProductoPaginadoResponse(SQLModel):
    total: int
    items: List[ProductoRead]

# ─── Operaciones con Ingredientes ─────────────────────────────────────────
class ProductoIngredienteAssign(SQLModel):
    """Schema para asignar ingrediente a producto existente"""
    ingrediente_id: int
    es_removible: bool = False
    cantidad: Decimal = Field(..., gt=0)

class ProductoIngredienteRemove(SQLModel):
    """Schema para remover ingrediente de producto"""
    ingrediente_id: int