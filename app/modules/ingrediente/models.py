from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from decimal import Decimal

if TYPE_CHECKING:
    from app.modules.producto.models import Producto
    from app.modules.unidad_medida.models import UnidadMedida


class IngredienteProductoLink(SQLModel, table=True):
    __tablename__ = "ingrediente_producto_link"
    
    ingrediente_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("ingrediente.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False
        )
    )

    producto_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("producto.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        )
    )
    es_removible: bool = Field(default=False, nullable=False)
    cantidad: Decimal = Field(..., gt=0)

    unidad_medida_id: int = Field(foreign_key="unidad_medida.id")
    unidad_medida: Optional["UnidadMedida"] = Relationship(back_populates="producto_ingredientes")

class Ingrediente(SQLModel, table=True):
    """
    Entidad Ingrediente.
    Relación N:M -> Un ingrediente puede pertenecer a múltiples productos.
    """

    __tablename__ = "ingrediente"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True, unique=True)
    descripcion: str = Field(default="")
    stock_cantidad: int = Field(default=0, ge=0, nullable=False)
    es_alergeno: bool = Field(default=False, nullable=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    productos: List["Producto"] = Relationship(
        back_populates="ingredientes",
        link_model=IngredienteProductoLink
    )
    activo: bool = Field(default=True, nullable=False)