from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, CHAR, Column, DateTime, String
from sqlmodel import Field, SQLModel


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
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    