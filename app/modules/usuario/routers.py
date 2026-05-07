from fastapi import APIRouter, Depends, Path, Query, status
from typing import Annotated, Optional
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from app.core.database import get_session
from . import schemas
from app.modules.usuario.services import UsuarioService

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


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
    response_model=schemas.Token,
    status_code=status.HTTP_200_OK,
)
def login(
    #credenciales: schemas.UsuarioLoginRequest,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    svs: UsuarioService = Depends(get_usuario_service),
):
    return svs.login(form_data.username, form_data.password)


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
