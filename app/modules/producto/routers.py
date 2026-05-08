from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from typing import List, Optional
from sqlmodel import Session
from app.core.database import get_session
from app.modules.producto.schemas import ProductoCategoriaAssign, ProductoRead, ProductoCreate, ProductoStockResponse, ProductoUpdate, ProductoPaginadoResponse, ProductoReadFull

from app.modules.producto.services import ProductoService

router = APIRouter(prefix="/productos", tags=["Productos"])

def get_producto_service(session: Session = Depends(get_session)) -> ProductoService:
    return ProductoService(session)

@router.post("/", response_model=ProductoRead, status_code=status.HTTP_201_CREATED)
def alta_producto(
    producto: ProductoCreate, 
    svc: ProductoService = Depends(get_producto_service)
) -> ProductoRead:
    print("Recibido en endpoint: ", producto)
    return svc.crear(data=producto)

@router.get("/", response_model=ProductoPaginadoResponse, status_code=status.HTTP_200_OK)
def listar_productos(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    nombre: Optional[str] = None,
    activo: Optional[bool] = None,
    svc: ProductoService = Depends(get_producto_service)
):
    return svc.obtener_todos(
        limit=limit,
        offset=offset,
        nombre=nombre,
        activo=activo,
    )


@router.get("/{id}", response_model=ProductoReadFull, status_code=status.HTTP_200_OK)
def detalle_producto(id: int = Path(..., gt=0), svc: ProductoService = Depends(get_producto_service)):
    producto = svc.obtener_por_id(id)
    return producto

@router.put("/{id}", response_model=ProductoRead, status_code=status.HTTP_200_OK)
def actualizar_producto(producto: ProductoUpdate, id: int = Path(..., gt=0), svc: ProductoService = Depends(get_producto_service)):
    actualizado = svc.actualizar(id, producto)
    return actualizado

@router.put("/{id}/desactivar", response_model=ProductoRead, status_code=status.HTTP_200_OK)
def borrado_logico(id: int = Path(..., gt=0), svc: ProductoService = Depends(get_producto_service)):
    desactivado = svc.deactive(producto_id=id)
    return desactivado

@router.get("/{id}/stock", response_model=ProductoStockResponse, status_code=status.HTTP_200_OK)
def consultar_stock(id: int = Path(..., gt=0), svc: ProductoService = Depends(get_producto_service)):
    resultado = svc.obtener_estado_stock(id)
    return resultado

# ─── Endpoints para la Relación N:M ─────────────────────────────────────────
@router.post("/{id}/categorias", response_model=ProductoRead, status_code=status.HTTP_200_OK)
def asignar_categoria(
    id: int, 
    body: ProductoCategoriaAssign, 
    svc: ProductoService = Depends(get_producto_service),
):
    producto = svc.agregar_categoria_a_producto(id, body.categoria_id, es_principal=body.es_principal)
    return producto

@router.delete("/{id}/categorias/{categoria_id}", response_model=ProductoRead, status_code=status.HTTP_200_OK)
def remover_categoria(id: int, categoria_id: int, svc: ProductoService = Depends(get_producto_service)):
    producto = svc.remover_categoria_de_producto(id, categoria_id)
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relación Producto-Categoría no encontrada")
    return producto