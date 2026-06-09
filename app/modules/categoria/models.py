from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlmodel import Field, Relationship, SQLModel

# Importamos la tabla intermedia desde producto.models
from app.modules.producto.models import ProductoCategoriaLink

if TYPE_CHECKING:
    # Solo para type hints, evita el import circular en tiempo de ejecución
    from app.modules.producto.models import Producto

class Categoria(SQLModel, table=True):
    """
    Entidad Categoria.
    Relación N:M -> Una categoría puede tener múltiples productos.
    """
    __tablename__ = "categoria"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True, unique=True)
    descripcion: str
    imagen_url: Optional[str] = Field(default=None, nullable=True)
    activo: bool = Field(default=True, nullable=False)

    created_at: datetime = Field( default_factory=lambda: datetime.now(datetime.UTC), nullable=False)
    updated_at: datetime = Field( default_factory=lambda: datetime.now(datetime.UTC), nullable=False)
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)

    # Autoreferencia
    parent_id: Optional[int] = Field(default=None, sa_column_kwargs={"nullable": True}, foreign_key="categoria.id")
    
    # Relación N:M con Producto
    productos: List["Producto"] = Relationship(
        back_populates="categorias",
        link_model=ProductoCategoriaLink
    )