from typing import TYPE_CHECKING, Optional
from sqlalchemy import Column, BigInteger, Sequence
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from decimal import Decimal

if TYPE_CHECKING:
    from app.modules.usuario.models import Usuario

class DireccionEntrega(SQLModel, table=True):
    
    __tablename__ = "direccionEntrega"
    
    id: Optional[int] = Field(
        default=None, 
        sa_column=Column(BigInteger, Sequence('direccion_id_seq'), primary_key=True)
    )
    usuario_id: int = Field(foreign_key="usuario.id", nullable=False)
    
    alias: Optional[str] = Field(max_length=50, default=None)
    linea1: str = Field(max_length=255, nullable=False)
    linea2: Optional[str] = Field(max_length=255, default=None)
    ciudad: str = Field(max_length=100, nullable=False)
    provincia: Optional[str] = Field(max_length=10, default=None)
    codigo_postal: str = Field(max_length=10)
    latitud: Optional[Decimal] = Field(max_digits=9, decimal_places=6, default=None)
    longitud: Optional[Decimal] = Field(max_digits=9, decimal_places=6, default=None)
    es_principal: bool = Field(default=False, nullable=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)
    
    # Relación de composición 0..* --> 1 Usuario
    usuario: Optional["Usuario"] = Relationship(back_populates="direcciones")