from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from typing import List, Optional
from sqlmodel import Session
from app.core.database import get_session
from . import schemas
from app.modules.categoria.services import CategoriaService

router = APIRouter(prefix="/categorias", tags=["Categorías"])

def get_categoria_service(session: Session = Depends(get_session)) -> CategoriaService:
    return CategoriaService(session)

@router.post(
    "/", 
    response_model=schemas.CategoriaRead, 
    status_code=status.HTTP_201_CREATED
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
    

@router.patch("/{id}", response_model=schemas.CategoriaRead, status_code=status.HTTP_200_OK)
def agregar_categoria_padre(
    id: int = Path(..., gt=0), 
    parent_id: int = Query(..., gt=0), 
    svs: CategoriaService = Depends(get_categoria_service)
):
    return svs.agregar_categoria_padre(id, parent_id)

@router.get("/{id}", response_model=schemas.CategoriaReadFull, status_code=status.HTTP_200_OK)
def detalle_categoria(id: int = Path(..., gt=0), svs: CategoriaService = Depends(get_categoria_service)):
    return svs.obtener_por_id(id)

@router.put("/{id}", response_model=schemas.CategoriaRead, status_code=status.HTTP_200_OK)
def actualizar_categoria(categoria: schemas.CategoriaUpdate, id: int = Path(..., gt=0), svs: CategoriaService = Depends(get_categoria_service)):
    actualizada = svs.actualizar_total(id, categoria)
    return actualizada

@router.put("/{id}/desactivar", response_model=schemas.CategoriaRead, status_code=status.HTTP_200_OK)
def borrado_logico(id: int = Path(..., gt=0), svs: CategoriaService = Depends(get_categoria_service)):
    return svs.desactivar(id)