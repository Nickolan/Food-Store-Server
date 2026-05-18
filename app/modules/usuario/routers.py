from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from typing import Annotated, Optional
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session
from app.core.database import get_session
from app.core.deps import get_current_active_user, require_role
from app.modules.usuario.models import Usuario
from . import schemas
from app.modules.usuario.services import UsuarioService

router = APIRouter(prefix="/api/v1/auth", tags=["Usuarios", "Auth"])
oauth2_scheme = HTTPBearer()

def get_usuario_service(session: Session = Depends(get_session)) -> UsuarioService:
    return UsuarioService(session)


@router.post(
    "/",
    response_model=schemas.UsuarioRead,
    status_code=status.HTTP_201_CREATED,
)
def registrar_usuario(
    usuario: schemas.UsuarioCreate,
    svs: UsuarioService = Depends(get_usuario_service),
):
    return svs.registrar_usuario(usuario)


@router.post(
    "/token",
    status_code=status.HTTP_200_OK,
)
def login(
    data: schemas.LoginRequest,
    response: Response,
    svs: UsuarioService = Depends(get_usuario_service),
):
    token = svs.authenticate(data.email, data.password)
    response.set_cookie(
        key="access_token",
        value=token.access_token,
        httponly=True,
        max_age=1800,  # 30 minutos, o el valor de expires_in
        samesite="lax",
        secure=False,  # En producción con HTTPS debería ser True
    )
    return {"mensaje": "Login exitoso. Sesión iniciada."}

@router.post("/logout")
def logout(response: Response):
    # Limpiar la cookie HttpOnly al cerrar sesión
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        secure=False,
    )
    return {"mensaje": "Sesión cerrada exitosamente"}

# ─── Rutas protegidas ────────────────────────────────────────────────────────

@router.get("/me", response_model=schemas.UsuarioRead)
def read_me(
    current_user: Annotated[Usuario, Depends(get_current_active_user)],
):
    return current_user


@router.get("/privado")
def ruta_privada(
    current_user: Annotated[Usuario, Depends(get_current_active_user)],
):
    return {
        "mensaje": f"¡Hola, {current_user.nombre}! Accediste a una ruta privada.",
    }


# ─── Rutas de administración (RBAC) ──────────────────────────────────────────

@router.get(
    "/",
    response_model=schemas.UsuarioPaginadoResponse,
    status_code=status.HTTP_200_OK,
)
def listar_usuarios(
     _admin: Annotated[Usuario, Depends(require_role(["admin"]))],
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    svs: UsuarioService = Depends(get_usuario_service),
):
    return svs.obtener_todos(offset=offset, limit=limit)


@router.get(
    "/{id}",
    response_model=schemas.UsuarioRead,
    status_code=status.HTTP_200_OK,
)
def detalle_usuario(
    id: int = Path(..., gt=0),
    svs: UsuarioService = Depends(get_usuario_service),
):
    return svs.obtener_por_id(id)


@router.put(
    "/{id}",
    response_model=schemas.UsuarioRead,
    status_code=status.HTTP_200_OK,
)
def actualizar_usuario(
    usuario: schemas.UsuarioUpdate,
    id: int = Path(..., gt=0),
    svs: UsuarioService = Depends(get_usuario_service),
):
    return svs.actualizar(id, usuario)


@router.delete(
    "/{id}",
    response_model=schemas.UsuarioRead,
    status_code=status.HTTP_200_OK,
)
def desactivar_usuario(
     _admin: Annotated[Usuario, Depends(require_role(["admin"]))],
    id: int = Path(..., gt=0),
    svs: UsuarioService = Depends(get_usuario_service),
):
    return svs.desactivar(id)
