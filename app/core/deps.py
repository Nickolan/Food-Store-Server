"""
Dependencias de autenticación y autorización para inyectar vía Depends().

Flujo de resolución:
    Request
      → oauth2_scheme extrae el Bearer token del header Authorization
      → get_current_user abre un UoW, decodifica el JWT, carga el usuario
      → get_current_active_user verifica que deleted_at es None
      → require_roles([...]) intercepta el token, lee los roles y verifica permisos.

Capa: Core (dependencias transversales)
Conoce a: UoW, Security, Model
"""

import logging
from typing import Annotated, List

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

logger = logging.getLogger("app.core.deps")

from app.core.security import decode_access_token
from app.core.unit_of_work import UnitOfWork
from app.modules.usuario.unit_of_work import UsuarioUnitOfWork, get_uow
from app.modules.usuario.models import Usuario
from app.core.database import get_session


class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> str | None:
        token = request.cookies.get("access_token")
        logger.debug("Token extraído de cookie: presente=%s", token is not None)
        if not token:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No autenticado",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return token

# Define el esquema OAuth2 que extrae el token de la cookie (o header)
oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/api/v6/auth/token")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Session = Depends(get_session)
) -> Usuario:
    """Decodifica el JWT y retorna el Usuario correspondiente."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    username: str | None = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    with UsuarioUnitOfWork(session) as uow:
        user = uow.usuarios.get_by_email(username)

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[Usuario, Depends(get_current_user)],
) -> Usuario:
    """Verifica que el usuario autenticado no esté desactivado."""
    logger.debug("Verificando usuario activo: id=%s", current_user.id)
    if current_user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cuenta de usuario desactivada",
        )
    return current_user


def require_roles(allowed_roles: List[str]):
    """
    Factory de dependencias para control de acceso basado en roles (RBAC).
    Lee los roles directamente del payload del JWT para mayor rendimiento.

    Uso:
        @router.get("/config", dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))])
    """
    async def role_checker(
        token: Annotated[str, Depends(oauth2_scheme)],
        current_user: Annotated[Usuario, Depends(get_current_active_user)],
    ) -> Usuario:
        
        # Obtenemos los roles incrustados en el token JWT
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
            
        user_roles = payload.get("roles", [])

        # Regla de Negocio UML: ADMIN tiene acceso total sin restricciones
        if "ADMIN" in user_roles:
            return current_user

        # Verificamos si hay alguna coincidencia entre los roles del usuario y los permitidos
        has_permission = any(role in allowed_roles for role in user_roles)

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Permisos insuficientes. Tus roles: {user_roles}. "
                    f"Se requiere al menos uno de: {allowed_roles}"
                ),
            )
            
        return current_user

    return role_checker


async def es_admin_o_stock(request: Request) -> bool:
    """
    Verifica si el token JWT en la request contiene roles ADMIN o STOCK.
    NO lanza excepción — retorna False si no hay token o no tiene permisos.
    Útil para endpoints públicos que cambian comportamiento según el rol.
    """
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        return False
    payload = decode_access_token(token)
    if not payload:
        return False
    user_roles = payload.get("roles", [])
    return "ADMIN" in user_roles or "STOCK" in user_roles
