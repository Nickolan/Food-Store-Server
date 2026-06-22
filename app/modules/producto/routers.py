from fastapi import APIRouter, Depends, HTTPException, Path, Query, status, UploadFile, File
from typing import List, Optional
from sqlmodel import Session
from app.core.cloudinary import subir_imagen
from app.core.database import get_session
from app.core.deps import require_roles, es_admin_o_stock
from app.modules.producto.schemas import (
    ProductoCategoriaAssign, 
    ProductoRead, 
    ProductoCreate, 
    ProductoStockResponse, 
    ProductoUpdate, 
    ProductoPaginadoResponse, 
    ProductoReadFull,
    ProductoMargenResponse,
    ProductoIngredienteAssign,
    ProductoAlertasResponse
) 

from app.modules.producto.services import ProductoService

router = APIRouter(prefix="/api/v6/productos", tags=["Productos"])

def get_producto_service(session: Session = Depends(get_session)) -> ProductoService:
    return ProductoService(session)

@router.post(
    "/", 
    response_model=ProductoRead, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))],
)
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




@router.get(
    "/alertas",
    response_model=ProductoAlertasResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))],
)
def listar_alertas(svc: ProductoService = Depends(get_producto_service)):
    """Retorna alertas livianas: productos con margen bajo o precio de ingrediente actualizado."""
    return svc.obtener_alertas()


@router.get("/{id}", response_model=ProductoReadFull, status_code=status.HTTP_200_OK)
def detalle_producto(
    id: int = Path(..., gt=0),
    svc: ProductoService = Depends(get_producto_service),
    es_admin: bool = Depends(es_admin_o_stock),
):
    producto = svc.obtener_por_id(id, calcular_alerta=es_admin)
    return producto

@router.put(
    "/{id}", 
    response_model=ProductoRead, 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))],
)
def actualizar_producto(producto: ProductoUpdate, id: int = Path(..., gt=0), svc: ProductoService = Depends(get_producto_service)):
    actualizado = svc.actualizar(id, producto)
    return actualizado

@router.put(
    "/{id}/desactivar", 
    response_model=ProductoRead, 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))],
)
def borrado_logico(id: int = Path(..., gt=0), svc: ProductoService = Depends(get_producto_service)):
    desactivado = svc.deactive(producto_id=id)
    return desactivado

@router.get(
    "/{id}/stock", 
    response_model=ProductoStockResponse, 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))],
)
def consultar_stock(id: int = Path(..., gt=0), svc: ProductoService = Depends(get_producto_service)):
    resultado = svc.obtener_estado_stock(id)
    return resultado

# ─── Endpoints para la Relación N:M con Categorías ─────────────────────────
@router.post(
    "/{id}/categorias", 
    response_model=ProductoRead, 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))],
)
def asignar_categoria(
    id: int, 
    body: ProductoCategoriaAssign, 
    svc: ProductoService = Depends(get_producto_service),
):
    producto = svc.agregar_categoria_a_producto(id, body.categoria_id, es_principal=body.es_principal)
    return producto

@router.delete(
    "/{id}/categorias/{categoria_id}", 
    response_model=ProductoRead, 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))],
)
def remover_categoria(id: int, categoria_id: int, svc: ProductoService = Depends(get_producto_service)):
    producto = svc.remover_categoria_de_producto(id, categoria_id)
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relación Producto-Categoría no encontrada")
    return producto

# ─── Nuevos Endpoints para la Relación N:M con Ingredientes ─────────────────
@router.post(
    "/{id}/ingredientes", 
    response_model=ProductoRead, 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))],
)
def asignar_ingrediente(
    id: int, 
    body: ProductoIngredienteAssign, 
    svc: ProductoService = Depends(get_producto_service),
):
    """Asigna un ingrediente a un producto indicando si es removible"""
    producto = svc.agregar_ingrediente_a_producto(
        id, 
        body.ingrediente_id, 
        es_removible=body.es_removible,
        cantidad=body.cantidad,
    )
    return producto

@router.put(
    "/{id}/ingredientes/{ingrediente_id}", 
    response_model=ProductoRead, 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))],
)
def actualizar_ingrediente_removible(
    id: int, 
    ingrediente_id: int,
    es_removible: bool = Query(..., description="True si el ingrediente puede ser removido, False si es fijo"),
    svc: ProductoService = Depends(get_producto_service),
):
    """Actualiza la propiedad es_removible de un ingrediente asociado al producto"""
    producto = svc.actualizar_ingrediente_removible(id, ingrediente_id, es_removible)
    return producto

@router.delete(
    "/{id}/ingredientes/{ingrediente_id}", 
    response_model=ProductoRead, 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))],
)
def remover_ingrediente(
    id: int, 
    ingrediente_id: int, 
    svc: ProductoService = Depends(get_producto_service)
):
    """Remueve un ingrediente de un producto"""
    producto = svc.remover_ingrediente_de_producto(id, ingrediente_id)
    return producto

@router.put(
    "/{id}/reactivar", 
    response_model=ProductoRead, 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))],
)
def reactivar_producto(
    id: int = Path(..., gt=0), 
    svc: ProductoService = Depends(get_producto_service)
):
    """Reactivar un producto previamente desactivado"""
    reactivado = svc.reactivar(producto_id=id)
    return reactivado


@router.get(
    "/{id}/categoria",
    response_model=ProductoPaginadoResponse,
    status_code=status.HTTP_200_OK,
)
def obtener_producto_por_categoria(
    id: int = Path(..., gt=0), 
    svc: ProductoService = Depends(get_producto_service)
):
    print(f"Obteniendo productos por categoría con ID: {id}")
    producto = svc.obtener_producto_por_categoria(categoria_id=id)
    return producto


@router.get(
    "/{id}/margen",
    response_model=ProductoMargenResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))],
)
def obtener_margen(id: int = Path(..., gt=0), svc: ProductoService = Depends(get_producto_service)):
    """Calcula el margen de ganancia del producto según el costo de sus ingredientes."""
    return svc.calcular_margen(id)


