from datetime import datetime
from typing import Optional

import bcrypt
from fastapi import HTTPException, status
from sqlmodel import Session
from app.core.security import decode_access_token, hash_password, verify_password, create_access_token

from .models import Usuario, UsuarioRol, Rol
from app.core.config import settings
from .schemas import (
    LoginResponse,
    UsuarioCreate,
    UsuarioPaginadoResponse,
    UsuarioRead,
    UsuarioUpdate,
    UsuarioLoginRequest,
    Token,
    AsignarRolRequest
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

    def _get_rol_or_404(self, uow: UsuarioUnitOfWork, rol_codigo: str):
        rol = uow.roles.get_by_codigo(rol_codigo)
        if not rol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El rol '{rol_codigo}' no existe en el catálogo.",
            )
        return rol

    def _hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def _verify_password(self, plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode(), hashed.encode())

    # ─── Casos de Uso (Usuarios) ───────────────────────────────────────────

    def registrar_usuario(self, data: UsuarioCreate) -> UsuarioRead:
        with UsuarioUnitOfWork(self._session) as uow:
            self._assert_email_unique(uow, data.email)

            rol_cliente = uow.roles.get_by_codigo("CLIENT")
            if not rol_cliente:
                rol_cliente = Rol(
                codigo="CLIENT",
                nombre="Cliente",
                descripcion="Cliente regular del sistema"
                )
                uow.roles.add(rol_cliente)
                uow.flush()  # para obtener el ID del rol_cliente

            nuevo = Usuario(
                nombre=data.nombre,
                apellido=data.apellido,
                email=data.email,
                celular=data.celular,
                password_hash=self._hash_password(data.password),
            )
            uow.usuarios.add(nuevo)
            uow.flush()  # para obtener el ID del nuevo usuario

            asignacion_rol = UsuarioRol(
                usuario_id=nuevo.id,
                rol_codigo=rol_cliente.codigo,
            )
            uow.usuario_roles.add(asignacion_rol)

            uow.flush()
            self._session.refresh(nuevo)  # para cargar relaciones y datos actualizados
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
            usuario.updated_at = datetime.now(datetime.UTC)
            uow.usuarios.add(usuario)
            uow.flush()
            result = UsuarioRead.model_validate(usuario)
        return result

    def desactivar(self, usuario_id: int) -> UsuarioRead:
        with UsuarioUnitOfWork(self._session) as uow:
            usuario = self._get_or_404(uow, usuario_id)
            usuario.deleted_at = datetime.now(datetime.UTC)
            usuario.updated_at = datetime.now(datetime.UTC)
            uow.usuarios.add(usuario)
            uow.flush()
            result = UsuarioRead.model_validate(usuario)
        return result
    
    def obtener_roles(self):
        """Devuelve el catálogo completo de roles disponibles."""
        with UsuarioUnitOfWork(self._session) as uow:
            return uow.roles.get_all_roles()

    def asignar_rol(self, usuario_id: int, request: AsignarRolRequest, asignado_por_id: int) -> UsuarioRead:
        with UsuarioUnitOfWork(self._session) as uow:
            usuario = self._get_or_404(uow, usuario_id)
            self._get_rol_or_404(uow, request.rol_codigo)

            asignacion_existente = uow.usuario_roles.get_asignacion(usuario_id, request.rol_codigo)
            if asignacion_existente:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El usuario ya posee el rol '{request.rol_codigo}'.",
                )

            nueva_asignacion = UsuarioRol(
                usuario_id=usuario_id,
                rol_codigo=request.rol_codigo,
                asignado_por_id=asignado_por_id,
                expires_at=request.expires_at
            )
            
            self._session.add(nueva_asignacion)
            uow.flush()
            self._session.refresh(usuario) 
            
            result = UsuarioRead.model_validate(usuario)
        return result

    def remover_rol(self, usuario_id: int, rol_codigo: str) -> UsuarioRead:
        with UsuarioUnitOfWork(self._session) as uow:
            usuario = self._get_or_404(uow, usuario_id)
            
            asignacion = uow.usuario_roles.get_asignacion(usuario_id, rol_codigo)
            if not asignacion:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"El usuario no tiene asignado el rol '{rol_codigo}'.",
                )

            self._session.delete(asignacion)
            uow.flush()
            self._session.refresh(usuario) 
            
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
            
            roles_usuario = [rol.codigo for rol in usuario.roles]
            
            access_token = create_access_token(
                data={
                    "sub": usuario.email, 
                    "id": usuario.id,
                    "roles": roles_usuario 
                }
            )
        return LoginResponse(mensaje="Login exitoso", usuario=result, access_token=access_token, expires_in=30 * 60)
       

    def get_usuario_from_token(self, token: str) -> UsuarioRead:
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido: falta 'sub'")
        with UsuarioUnitOfWork(self._session) as uow:
            usuario = uow.usuarios.get_by_email(email)
            if not usuario or usuario.deleted_at is not None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado o desactivado")
            return UsuarioRead.model_validate(usuario)

    def authenticate(self, username: str, password: str) -> Token:
        """Autentica con username + password y retorna un Token con JWT."""
        with UsuarioUnitOfWork(self._session) as uow:
            usuario = uow.usuarios.get_by_email(username)

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
            roles_usuario = [rol.codigo for rol in usuario.roles]
            access_token = create_access_token(
                data={"sub": usuario.email, 'id': usuario.id, "roles": roles_usuario}
            )
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
