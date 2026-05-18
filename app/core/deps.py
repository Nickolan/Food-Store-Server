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

from typing import Annotated, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token
from app.core.unit_of_work import UnitOfWork
from app.modules.usuario.unit_of_work import get_uow
from app.modules.usuario.models import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/usuarios/login")  # Endpoint de login para obtener el token


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
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

    with uow:
        user = uow.usuarios.get_by_email(username)

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[Usuario, Depends(get_current_user)],
) -> Usuario:
    """Verifica que el usuario autenticado no esté desactivado."""
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
