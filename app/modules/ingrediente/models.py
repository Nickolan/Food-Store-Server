from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import Column, ForeignKey, Integer

from sqlmodel import Field, Relationship, SQLModel

from datetime import datetime



if TYPE_CHECKING:

    from app.modules.producto.models import Producto





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



class Ingrediente(SQLModel, table=True):

    """

    Entidad Ingrediente.

    Relación N:M -> Un ingrediente puede pertenecer a múltiples productos.

    """



    __tablename__ = "ingrediente"



    id: Optional[int] = Field(default=None, primary_key=True)

    nombre: str = Field(index=True)

    descripcion: str

    es_alergeno: bool = Field(default=False, nullable=True)

   

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)



    productos: List["Producto"] = Relationship(

        back_populates="ingredientes",

        link_model=IngredienteProductoLink

    )

    activo: bool = Field(default=True, nullable=False)