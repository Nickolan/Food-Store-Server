from fastapi import APIRouter, Depends, Path, Query, status
from typing import Annotated, Optional, List
from sqlmodel import Session
from app.core.database import get_session
from app.core.deps import get_current_active_user
from app.modules.usuario.models import Usuario
from . import schemas
from app.modules.usuario.services import UsuarioService

router = APIRouter(prefix="/usuarios", tags=["Usuarios", "Auth"])


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
    credenciales: schemas.UsuarioLoginRequest,
    svs: UsuarioService = Depends(get_usuario_service),
):
    return svs.login(credenciales.email, credenciales.password)


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

@router.get(
    "/roles",
    response_model=List[schemas.RolRead],
    status_code=status.HTTP_200_OK,
)
def listar_roles(
    svs: UsuarioService = Depends(get_usuario_service),
):
    return svs.obtener_roles()


@router.post(
    "/{id}/roles",
    response_model=schemas.UsuarioRead,
    status_code=status.HTTP_201_CREATED,
)
def asignar_rol_a_usuario(
    request: schemas.AsignarRolRequest,
    id: int = Path(..., gt=0),
    svs: UsuarioService = Depends(get_usuario_service),
    current_user: Usuario = Depends(get_current_active_user),
):
    return svs.asignar_rol(
        usuario_id=id, 
        request=request, 
        asignado_por_id=current_user.id
    )


@router.delete(
    "/{id}/roles/{rol_codigo}",
    response_model=schemas.UsuarioRead,
    status_code=status.HTTP_200_OK,
)
def remover_rol_de_usuario(
    rol_codigo: str,
    id: int = Path(..., gt=0),
    svs: UsuarioService = Depends(get_usuario_service),
):
    return svs.remover_rol(usuario_id=id, rol_codigo=rol_codigo)


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