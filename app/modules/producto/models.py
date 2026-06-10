from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Column, ForeignKey, Integer
from sqlmodel import JSON, Field, Relationship, SQLModel

from app.modules.ingrediente.models import IngredienteProductoLink

if TYPE_CHECKING:
    from app.modules.categoria.models import Categoria
    from app.modules.ingrediente.models import Ingrediente
    from app.modules.unidad_medida.models import UnidadMedida

# ─────────────────────────────────────────────────────────────────────────────
# Tabla de enlace N:M  →  Producto ↔ Categoria
# ─────────────────────────────────────────────────────────────────────────────
class ProductoCategoriaLink(SQLModel, table=True):
    """
    Relación N:M entre Producto y Categoria.
    PK compuesta evita duplicados. ondelete='CASCADE' limpia enlaces huérfanos.
    """
    __tablename__ = "producto_categoria_link"

    producto_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("producto.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        )
    )
    categoria_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("categoria.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        )
    )

    es_principal: bool = Field(default=False, nullable=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

# ─────────────────────────────────────────────────────────────────────────────
# Producto
# ─────────────────────────────────────────────────────────────────────────────
class Producto(SQLModel, table=True):
    """
    Entidad Producto.
    Relación N:M -> Un producto puede pertenecer a múltiples categorías.
    """
    __tablename__ = "producto"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True)
    descripcion: str = Field(default="", nullable=False)
    precio_base: float = Field(default=0.0, nullable=False, gt=0)
    stock: int = Field(default=0)
    stock_minimo: int = Field(default=0)
    imagenes_url: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    activo: bool = Field(default=True, nullable=False)
    disponible: bool = Field(default=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)

    unidad_venta_id: Optional[int] = Field(default=None, foreign_key="unidad_medida.id")
    unidad_medida: Optional["UnidadMedida"] = Relationship(back_populates="productos")

    # Relación N:M con Categoria via ProductoCategoriaLink
    categorias: List["Categoria"] = Relationship(
        back_populates="productos",
        link_model=ProductoCategoriaLink
    )

    # Relacion N:M con Ingrediente via IngredienteProductoLink
    ingredientes: List["Ingrediente"] = Relationship(
        back_populates="productos",
        link_model=IngredienteProductoLink
    )