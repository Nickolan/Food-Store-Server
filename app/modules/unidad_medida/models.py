from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import BIGINT, TIMESTAMP

if TYPE_CHECKING:
    from app.modules.producto.models import Producto
    from app.modules.ingrediente.models import Ingrediente
    from app.modules.ingrediente.models import IngredienteProductoLink

class UnidadMedida(SQLModel, table=True):
    __tablename__ = "unidad_medida"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BIGINT, primary_key=True, autoincrement=True)
    )
    nombre: str = Field(sa_column=Column(String(50), unique=True, nullable=False))
    simbolo: str = Field(sa_column=Column(String(10), unique=True, nullable=False))
    tipo: str = Field(sa_column=Column(String(20), nullable=False))
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    )

    productos: List["Producto"] = Relationship(back_populates="unidad_medida")
    ingredientes: List["Ingrediente"] = Relationship(back_populates="unidad_medida")