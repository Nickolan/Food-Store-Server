from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from typing import List, Optional
from sqlmodel import Session
from app.core.database import get_session
from app.modules.ingrediente.schemas import IngredienteCreate, IngredienteProductoAssign, IngredienteRead, IngredienteReadFull, IngredienteUpdate, IngredientePaginadoResponse
from app.modules.ingrediente.services import IngredienteService

router = APIRouter(prefix="/ingredientes", tags=["Ingredientes"])

def get_ingrediente_service(session: Session = Depends(get_session)) -> IngredienteService:
    return IngredienteService(session)

@router.post("/", response_model=IngredienteRead, status_code=status.HTTP_201_CREATED)
def crear_ingrediente(
    ingrediente: IngredienteCreate, 
    svc: IngredienteService = Depends(get_ingrediente_service)
) -> IngredienteRead:
    return svc.crear(ingrediente)

@router.get("/", response_model=IngredientePaginadoResponse, status_code=status.HTTP_200_OK)
def listar_ingredientes(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    # nombre: Optional[str] = None,
    svc: IngredienteService = Depends(get_ingrediente_service)
):
    return svc.listar(
        offset=offset,
        limit=limit
    )

@router.get("/{id}", response_model=IngredienteReadFull, status_code=status.HTTP_200_OK)
def detalle_ingrediente(id: int = Path(..., gt=0), svc: IngredienteService = Depends(get_ingrediente_service)):
    ingrediente = svc.obtener_por_id(id)
    return ingrediente

@router.put("/{id}", response_model=IngredienteRead, status_code=status.HTTP_200_OK)
def actualizar_ingrediente(ingrediente: IngredienteUpdate, id: int = Path(..., gt=0), svc: IngredienteService = Depends(get_ingrediente_service)):
    actualizado = svc.actualizar(ingrediente_id=id, data=ingrediente)
    return actualizado

@router.delete("/{id}", response_model=IngredienteRead, status_code=status.HTTP_200_OK)
def eliminar_ingrediente(id: int = Path(..., gt=0), svc: IngredienteService = Depends(get_ingrediente_service)) -> IngredienteRead:
    return svc.desactivar(ingrediente_id=id)

# ─── Endpoints para la Relación N:M ─────────────────────────────────────────
@router.post("/{id}/productos", response_model=IngredienteReadFull)
def asignar_producto(
    id: int, 
    body: IngredienteProductoAssign, 
    svc: IngredienteService = Depends(get_ingrediente_service),
):
    resultado = svc.agregar_a_producto(ingrediente_id=id, body=body)
    return resultado

@router.delete("/{id}/productos", response_model=IngredienteReadFull)
def remover_producto(
    id: int, 
    body: IngredienteProductoAssign, 
    svc: IngredienteService = Depends(get_ingrediente_service),
):
    resultado = svc.remover_de_producto(ingrediente_id=id, producto_id=body.producto_id)
    return resultado
