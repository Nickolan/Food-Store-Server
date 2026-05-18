from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.usuario.models import Usuario

class Direccion(SQLModel, table=True):
    __tablename__ = "direccion"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", nullable=False)
    calle: str = Field(max_length=255, nullable=False)
    numero: int = Field(nullable=False)
    ciudad: str = Field(max_length=100, nullable=False)
    codigo_postal: str = Field(max_length=20, nullable=False)
    es_principal: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
    # Relación con Usuario
    usuario: Optional["Usuario"] = Relationship(back_populates="direcciones")