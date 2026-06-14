from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from typing import Annotated, Optional, List
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session
from app.core.database import get_session
from app.core.deps import get_current_active_user, require_roles
from app.modules.usuario.models import Usuario
from . import schemas
from app.modules.usuario.services import UsuarioService

router = APIRouter(prefix="/api/v6/auth", tags=["Usuarios", "Auth"])
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
    response: Response,
    svs: UsuarioService = Depends(get_usuario_service),
):
    usuarioNuevo = svs.registrar_usuario(usuario)
    token = svs.authenticate(usuario.email, usuario.password)
    response.set_cookie(
        key="access_token",
        value=token.access_token,
        httponly=True,
        max_age=1800,
        samesite="lax",
        secure=False,
        path="/"
    )
    return usuarioNuevo


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
        max_age=1800,
        samesite="lax",
        secure=False,
        path="/"
    )
    return {"mensaje": "Login exitoso. Sesión iniciada."}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        secure=False,
        path="/"
    )
    return {"mensaje": "Sesión cerrada exitosamente"}


@router.get("/me", response_model=schemas.UsuarioRead)
def read_me(
    current_user: Annotated[Usuario, Depends(get_current_active_user)],
):
    return current_user


@router.put(
    "/me",
    response_model=schemas.UsuarioRead,
    status_code=status.HTTP_200_OK,
)
def actualizar_mis_datos(
    usuario: schemas.UsuarioUpdate,
    current_user: Annotated[Usuario, Depends(get_current_active_user)],
    svs: UsuarioService = Depends(get_usuario_service),
):
    return svs.actualizar(current_user.id, usuario)


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
    dependencies=[Depends(require_roles(["ADMIN"]))],
)
def listar_roles(
    svs: UsuarioService = Depends(get_usuario_service),
):
    return svs.obtener_roles()


@router.post(
    "/{id}/roles",
    response_model=schemas.UsuarioRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(["ADMIN"]))],
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
    dependencies=[Depends(require_roles(["ADMIN"]))],
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
    dependencies=[Depends(require_roles(["ADMIN"]))],
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
    dependencies=[Depends(require_roles(["ADMIN"]))],
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
    current_user: Usuario = Depends(get_current_active_user),
):
    if current_user.id != id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar este usuario",
        )
    return svs.actualizar(id, usuario)


@router.delete(
    "/{id}",
    response_model=schemas.UsuarioRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(["ADMIN"]))],
)
def desactivar_usuario(
    id: int = Path(..., gt=0),
    svs: UsuarioService = Depends(get_usuario_service),
):
    return svs.desactivar(id)


@router.patch(
    "/{id}/activar",
    response_model=schemas.UsuarioRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(["ADMIN"]))],
)
def reactivar_usuario(
    id: int = Path(..., gt=0),
    svs: UsuarioService = Depends(get_usuario_service),
):
    return svs.reactivar(id)