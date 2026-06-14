from fastapi import APIRouter, Depends, HTTPException, Path, Query, status, UploadFile, File
from typing import List, Optional
from sqlmodel import Session
from app.core.database import get_session
from app.core.deps import require_roles
from . import schemas
from app.modules.categoria.services import CategoriaService
from app.core.cloudinary import subir_imagen, eliminar_imagen
from urllib.parse import unquote

router = APIRouter(prefix="/categorias", tags=["Categorías"])

def get_categoria_service(session: Session = Depends(get_session)) -> CategoriaService:
    return CategoriaService(session)

@router.post(
    "/", 
    response_model=schemas.CategoriaRead, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))],
)
def alta_categoria(
    categoria: schemas.CategoriaCreate, 
    svs: CategoriaService = Depends(get_categoria_service)
):
    return svs.crear_categoria(categoria)

@router.get("/", response_model=schemas.CategoriaPaginadoResponse, status_code=status.HTTP_200_OK)
def listar_categorias(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    nombre: Optional[str] = None,
    svs: CategoriaService = Depends(get_categoria_service)
):
    return svs.obtener_todas(
        offset=offset,
        limit=limit,
        nombre=nombre
    )
    

@router.patch(
    "/{id}", 
    response_model=schemas.CategoriaRead, 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))],
)
def agregar_categoria_padre(
    id: int = Path(..., gt=0), 
    parent_id: int = Query(..., gt=0), 
    svs: CategoriaService = Depends(get_categoria_service)
):
    return svs.agregar_categoria_padre(id, parent_id)

@router.get(
    "/{id}", 
    response_model=schemas.CategoriaReadFull, 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(["ADMIN"]))],
)
def detalle_categoria(id: int = Path(..., gt=0), svs: CategoriaService = Depends(get_categoria_service)):
    return svs.obtener_por_id(id)

@router.put(
    "/{id}", 
    response_model=schemas.CategoriaRead, 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))],
)
def actualizar_categoria(categoria: schemas.CategoriaUpdate, id: int = Path(..., gt=0), svs: CategoriaService = Depends(get_categoria_service)):
    actualizada = svs.actualizar_total(id, categoria)
    return actualizada

@router.put(
    "/{id}/desactivar", 
    response_model=schemas.CategoriaRead, 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))],
)
def borrado_logico(id: int = Path(..., gt=0), svs: CategoriaService = Depends(get_categoria_service)):
    return svs.desactivar(id)

@router.post(
    "/{id}/imagen",
    response_model=schemas.CategoriaRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))],
)
async def subir_imagen_categoria(
    id: int = Path(..., gt=0),
    file: UploadFile = File(...),
    svs: CategoriaService = Depends(get_categoria_service)
):
    contenido = await file.read()
    result = subir_imagen(
        file_bytes=contenido,
        content_type=file.content_type,
        carpeta="foodstore/categorias"
    )
    data = schemas.CategoriaUpdate(imagen_url=result["secure_url"])
    return svs.actualizar_total(id, data)

@router.delete(
    "/{id}/imagen",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))],
)
async def eliminar_imagen_categoria(
    id: int = Path(..., gt=0),
    public_id: str = Query(...),
    svs: CategoriaService = Depends(get_categoria_service)
):
    eliminar_imagen(unquote(public_id))
    data = schemas.CategoriaUpdate(imagen_url=None)
    svs.actualizar_total(id, data)