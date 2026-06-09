from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import BigInteger, CHAR, Column, DateTime, String, ForeignKey, Text
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from app.modules.direccionEntrega.models import DireccionEntrega


class UsuarioRol(SQLModel, table=True):
    __tablename__ = "usuario_rol"

    usuario_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("usuario.id"), primary_key=True, nullable=False)
    )
    rol_codigo: str = Field(
        sa_column=Column(String(20), ForeignKey("rol.codigo"), primary_key=True, nullable=False)
    )
    
    asignado_por_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("usuario.id"), nullable=True)
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(datetime.UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )


class Rol(SQLModel, table=True):
    __tablename__ = "rol"

    codigo: str = Field(
        sa_column=Column(String(20), primary_key=True, nullable=False)
    )
    
    nombre: str = Field(
        sa_column=Column(String(50), unique=True, nullable=False)
    )
    descripcion: Optional[str] = Field(
        default=None, 
        sa_column=Column(Text, nullable=True)
    )

    usuarios: List["Usuario"] = Relationship(
        back_populates="roles", 
        link_model=UsuarioRol,
        sa_relationship_kwargs={
            "primaryjoin": "Rol.codigo == UsuarioRol.rol_codigo",
            "secondaryjoin": "Usuario.id == UsuarioRol.usuario_id"
        }
    )


class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, nullable=False),
    )
    
    nombre: str = Field(sa_column=Column(String(80), nullable=False))
    apellido: str = Field(sa_column=Column(String(80), nullable=False))
    email: str = Field(sa_column=Column(String(254), unique=True, nullable=False))
    celular: Optional[str] = Field(default=None, sa_column=Column(String(20), nullable=True))
    password_hash: str = Field(sa_column=Column(CHAR(60), nullable=False))

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(datetime.UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(datetime.UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    roles: List[Rol] = Relationship(
        back_populates="usuarios", 
        link_model=UsuarioRol,
        sa_relationship_kwargs={
            "primaryjoin": "Usuario.id == UsuarioRol.usuario_id",
            "secondaryjoin": "Rol.codigo == UsuarioRol.rol_codigo"
        }
    )
    # Relación con DireccionEntrega
    direcciones: List["DireccionEntrega"] = Relationship(back_populates="usuario")
    
