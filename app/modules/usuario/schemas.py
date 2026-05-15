from typing import List, Optional
from pydantic import Field, EmailStr
from sqlmodel import SQLModel
from datetime import datetime

# ─── Base ──────────────────────────────────────────────────────────────────
class UsuarioBase(SQLModel):
    nombre: str = Field(..., min_length=1, max_length=80, examples=["Juan"])
    apellido: str = Field(..., min_length=1, max_length=80, examples=["Pérez"])
    email: EmailStr = Field(..., examples=["juan.perez@example.com"])
    celular: Optional[str] = Field(default=None, max_length=20, examples=["+541112345678"])

# ─── Request schemas ───────────────────────────────────────────────────────
class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=8, examples=["S3cur3P@ss!"])

class UsuarioUpdate(SQLModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=80, examples=["Juan"])
    apellido: Optional[str] = Field(None, min_length=1, max_length=80, examples=["Pérez"])
    celular: Optional[str] = Field(None, max_length=20, examples=["+541112345678"])

class UsuarioLoginRequest(SQLModel):
    email: str = Field(..., examples=["juan.perez@example.com"])
    password: str = Field(..., examples=["S3cur3P@ss!"])

# ─── Response schemas ──────────────────────────────────────────────────────
class UsuarioRead(UsuarioBase):
    id: int
    created_at: datetime
    updated_at: datetime

class UsuarioPaginadoResponse(SQLModel):
    total: int
    items: List[UsuarioRead]


class Token(SQLModel):
    """Respuesta del endpoint /token."""
    access_token: str
    token_type:   str = "bearer"
    expires_in:   int  # segundos hasta expiración

class LoginResponse(Token):
    mensaje: str = Field(examples=["Login exitoso"])
    usuario: UsuarioRead

class LoginRequest(SQLModel):
    email: str
    password: str