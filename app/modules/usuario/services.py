from datetime import datetime
from typing import Optional

import bcrypt
from fastapi import HTTPException, status
from sqlmodel import Session
from app.core.security import hash_password, verify_password, create_access_token

from .models import Usuario
from app.core.config import settings
from .schemas import (
    LoginResponse,
    UsuarioCreate,
    UsuarioPaginadoResponse,
    UsuarioRead,
    UsuarioUpdate,
    UsuarioLoginRequest,
    Token
)
from app.modules.usuario.unit_of_work import UsuarioUnitOfWork


class UsuarioService:
    def __init__(self, session: Session) -> None:
        self._session = session

    # ─── Helpers ───────────────────────────────────────────────────────────

    def _get_or_404(self, uow: UsuarioUnitOfWork, usuario_id: int) -> Usuario:
        usuario = uow.usuarios.get_by_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con id={usuario_id} no encontrado",
            )
        return usuario

    def _assert_email_unique(self, uow: UsuarioUnitOfWork, email: str) -> None:
        existing = uow.usuarios.get_by_email(email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un usuario con email='{email}'",
            )

    def _hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def _verify_password(self, plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode(), hashed.encode())

    # ─── Casos de Uso ──────────────────────────────────────────────────────

    def registrar_usuario(self, data: UsuarioCreate) -> UsuarioRead:
        with UsuarioUnitOfWork(self._session) as uow:
            self._assert_email_unique(uow, data.email)
            nuevo = Usuario(
                nombre=data.nombre,
                apellido=data.apellido,
                email=data.email,
                celular=data.celular,
                password_hash=self._hash_password(data.password),
            )
            uow.usuarios.add(nuevo)
            result = UsuarioRead.model_validate(nuevo)
        return result

    def obtener_todos(self, offset: int = 0, limit: int = 20) -> UsuarioPaginadoResponse:
        with UsuarioUnitOfWork(self._session) as uow:
            usuarios = uow.usuarios.get_activos(offset=offset, limit=limit)
            total = uow.usuarios.count_activos()
            items = [UsuarioRead.model_validate(u) for u in usuarios]
        return UsuarioPaginadoResponse(total=total, items=items)

    def obtener_por_id(self, usuario_id: int) -> UsuarioRead:
        with UsuarioUnitOfWork(self._session) as uow:
            usuario = self._get_or_404(uow, usuario_id)
            result = UsuarioRead.model_validate(usuario)
        return result

    def actualizar(self, usuario_id: int, data: UsuarioUpdate) -> UsuarioRead:
        with UsuarioUnitOfWork(self._session) as uow:
            usuario = self._get_or_404(uow, usuario_id)
            cambios = data.model_dump(exclude_unset=True)
            for key, value in cambios.items():
                setattr(usuario, key, value)
            usuario.updated_at = datetime.utcnow()
            uow.usuarios.add(usuario)
            result = UsuarioRead.model_validate(usuario)
        return result

    def desactivar(self, usuario_id: int) -> UsuarioRead:
        with UsuarioUnitOfWork(self._session) as uow:
            usuario = self._get_or_404(uow, usuario_id)
            usuario.deleted_at = datetime.utcnow()
            usuario.updated_at = datetime.utcnow()
            uow.usuarios.add(usuario)
            result = UsuarioRead.model_validate(usuario)
        return result

    def login(self, email: str, password: str) -> LoginResponse:
        with UsuarioUnitOfWork(self._session) as uow:
            usuario = uow.usuarios.get_by_email(email)
            if not usuario or not self._verify_password(password, usuario.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales inválidas",
                )
            if usuario.deleted_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="El usuario está desactivado",
                )
            result = UsuarioRead.model_validate(usuario)
            access_token = create_access_token(
                data={"sub": usuario.email, 'id': usuario.id}
            )
        return LoginResponse(mensaje="Login exitoso", usuario=result)
        # return Token(
        #     access_token=access_token,
        #     token_type="bearer",
        #     expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        # )
