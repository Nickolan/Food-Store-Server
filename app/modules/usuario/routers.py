from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from typing import Annotated, Optional
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session
from app.core.database import get_session
from app.core.deps import get_current_active_user
from app.modules.usuario.models import Usuario
from . import schemas
from app.modules.usuario.services import UsuarioService

router = APIRouter(prefix="/usuarios", tags=["Usuarios", "Auth"])
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
    "/login",
    response_model=schemas.LoginResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    data: schemas.LoginRequest,
    svs: UsuarioService = Depends(get_usuario_service),
):
    return svs.login(data.email, data.password)


# Rutas Protegidas (requieren autenticación) - Ejemplo de uso de get_current_active_user
@router.get("/me", response_model=schemas.UsuarioRead)
def read_me(
    token: HTTPAuthorizationCredentials | None = Depends(oauth2_scheme),
    svs: UsuarioService = Depends(get_usuario_service),
):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token no proporcionado")
    return svs.get_usuario_from_token(token.credentials)

@router.get("/privado")
def ruta_privada(
    token: HTTPAuthorizationCredentials | None = Depends(oauth2_scheme),
    svs: UsuarioService = Depends(get_usuario_service),
):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token no proporcionado")
    current_user = svs.get_usuario_from_token(token.credentials)
    return {
        "mensaje": f"¡Hola, {current_user.nombre}! Accediste a una ruta privada.",
    }


@router.get(
    "/",
    response_model=schemas.UsuarioPaginadoResponse,
    status_code=status.HTTP_200_OK,
)
def listar_usuarios(
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
    id: int = Path(..., gt=0),
    svs: UsuarioService = Depends(get_usuario_service),
):
    return svs.desactivar(id)
