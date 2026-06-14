from datetime import datetime, timezone
from typing import List, Optional, Tuple
from decimal import Decimal
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from sqlmodel import Session, select, func

from .models import Producto, ProductoCategoriaLink
from .schemas import (
    ProductoRead, ProductoCreate, ProductoUpdate, 
    ProductoPaginadoResponse, ProductoReadFull, 
    CategoriaWithPrincipal, IngredienteWithProductoInfo,
    ProductoIngredienteAssign, ProductoIngredienteCreate
)
from app.modules.categoria.models import Categoria
from app.modules.ingrediente.models import Ingrediente
from app.modules.producto.unit_of_work import ProductoUnitOfWork

class ProductoService:
    def __init__(self, session: Session) -> None:
        self._session = session

    # Helpers privados
    def _get_or_404(self, uof: ProductoUnitOfWork, producto_id: int) -> Producto:
        producto = uof.productos.get_by_id(producto_id)
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {producto_id} no encontrado."
            )
        return producto
    
    def _get_full_or_404(self, uof: ProductoUnitOfWork, producto_id: int) -> Producto:
        producto = uof.productos.get_full_by_id(producto_id)
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {producto_id} no encontrado."
            )
        return producto
    
    def _get_categoria_or_404(self, uof: ProductoUnitOfWork, categoria_id: int) -> Categoria:
        categoria = uof.categorias.get_by_id(categoria_id)
        if not categoria:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categoria con ID {categoria_id} no encontrada."
            )
        return categoria
    
    def _get_ingrediente_or_404(self, uof: ProductoUnitOfWork, ingrediente_id: int) -> Ingrediente:
        ingrediente = uof.ingredientes.get_by_id(ingrediente_id)
        if not ingrediente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ingrediente con ID {ingrediente_id} no encontrado."
            )
        return ingrediente

    def _assert_link_not_exists(self, uof: ProductoUnitOfWork, producto_id: int, categoria_id: int):
        link = uof.productos.get_link(producto_id, categoria_id)
        if link:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El producto {producto_id} ya tiene asignada la categoría {categoria_id}."
            )
    
    def _assert_ingrediente_link_not_exists(self, uof: ProductoUnitOfWork, producto_id: int, ingrediente_id: int):
        link = uof.productos.get_ingrediente_link(producto_id, ingrediente_id)
        if link:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El producto {producto_id} ya tiene asignado el ingrediente {ingrediente_id}."
            )

    def _validar_stock_ingredientes(
        self,
        uof: ProductoUnitOfWork,
        ingredientes: List[ProductoIngredienteCreate],
    ) -> None:
        """
        Valida que haya stock suficiente para cada ingrediente requerido.
        Recolecta TODOS los faltantes antes de lanzar la excepción,
        para que el cliente vea el problema completo de una sola vez.
        """
        faltantes = []

        for ing_data in ingredientes:
            ingrediente = uof.ingredientes.get_by_id(ing_data.ingrediente_id)

            if not ingrediente:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ingrediente con ID {ing_data.ingrediente_id} no encontrado."
                )

            if ingrediente.stock_cantidad < ing_data.cantidad:
                faltantes.append({
                    "ingrediente_id": ingrediente.id,
                    "nombre": ingrediente.nombre,
                    "stock_disponible": ingrediente.stock_cantidad,
                    "cantidad_requerida": float(ing_data.cantidad),
                    "faltante": float(ing_data.cantidad - ingrediente.stock_cantidad),
                })

        if faltantes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "mensaje": "Stock insuficiente para uno o más ingredientes.",
                    "ingredientes_sin_stock": faltantes,
                },
            )
    def calcular_stock_por_ingredientes(self,uow:ProductoUnitOfWork, producto_id:int) -> Optional[int]:
        """
    Calcula cuántas unidades del producto se pueden fabricar
    según el stock actual de sus ingredientes.
    Retorna None si el producto no tiene ingredientes (usar producto.stock como fallback).
    """
        links=uow.productos.get_all_ingrediente_links(producto_id)
        if not links:
            return None  # No hay ingredientes, no se puede calcular stock por ingredientes
        minimo=None
        for link in links:
            if not link.cantidad or link.cantidad == 0:
                continue  # Evitar división por cero
            ingrediente=uow.ingredientes.get_by_id(link.ingrediente_id)
            if not ingrediente:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ingrediente con ID {link.ingrediente_id} no encontrado.")
            fabricables=ingrediente.stock_cantidad // link.cantidad
            if minimo is None or fabricables < minimo:
                minimo = fabricables
        return minimo if minimo is not None else 0
   
    # Casos de uso

    def crear(self, data: ProductoCreate) -> ProductoRead:
        with ProductoUnitOfWork(self._session) as uow:
            # Validar stock de ingredientes ANTES de cualquier INSERT
            if data.ingredientes:
                self._validar_stock_ingredientes(uow, data.ingredientes)

            # Crear producto base
            nuevo = Producto.model_validate(data.dict(exclude={'ingredientes', 'categorias_ids'}))
            print("Nuevo producto: ", nuevo)
            uow.productos.add(nuevo)
            uow.flush()  # Para obtener el ID del producto
            
            # Asignar ingredientes si vienen en la creación
            if data.ingredientes:
                for ing_data in data.ingredientes:
                    # Verificar que el ingrediente existe
                    ingrediente = self._get_ingrediente_or_404(uow, ing_data.ingrediente_id)
                    # Crear link
                    uow.productos.link_ingrediente(
                        producto_id=nuevo.id, 
                        ingrediente_id=ing_data.ingrediente_id, 
                        es_removible=ing_data.es_removible,
                        cantidad=ing_data.cantidad,
                    )
            if data.categorias_ids:
                print("Asignando categorías al producto: ", data.categorias_ids)
                for categoria_id in data.categorias_ids:
                    # Verificar que la categoría existe
                    categoria = self._get_categoria_or_404(uow, categoria_id)
                    # Crear link (por defecto no es principal al crear)
                    uow.productos.link_categoria(
                        producto_id=nuevo.id,
                        categoria_id=categoria_id,
                        es_principal=False
                    )

            result = ProductoRead.model_validate(nuevo)
            print("Producto creado: ", result)
        return result
    
    def obtener_todos(self, offset: int = 0, limit: int = 20, nombre: Optional[str] = None, activo: Optional[bool] = None) -> ProductoPaginadoResponse:
        with ProductoUnitOfWork(self._session) as uow:
            productos = uow.productos.get_paginado(offset=offset, limit=limit, nombre=nombre, activo=activo)
            total = uow.productos.count(nombre=nombre, activo=activo)

            result = ProductoPaginadoResponse(
                items=[ProductoRead.model_validate(p) for p in productos],
                total=total
            )
        return result
    
    def obtener_por_id(self, producto_id: int) -> ProductoReadFull:
        with ProductoUnitOfWork(self._session) as uow:
            producto = self._get_full_or_404(uow, producto_id)

            # validar por cada categoría si es principal o no mediante ProductoCategoriaLink
            response_categorias = []
            for categoria in producto.categorias:
                link = uow.productos.get_link(producto_id, categoria.id)
                response_categorias.append(CategoriaWithPrincipal(
                    categoria=categoria.model_dump(),
                    es_principal=link.es_principal == True if link else False
                ))

            
            response_ingredientes = []
            for ingrediente in producto.ingredientes:
                link = uow.productos.get_ingrediente_link(producto_id, ingrediente.id)
                response_ingredientes.append(IngredienteWithProductoInfo(
                    ingrediente=ingrediente.model_dump(),
                    es_removible=link.es_removible == True if link else False,
                    cantidad=link.cantidad if link else None,
                ))

            print("Producto: ", producto)
            unidad_medida = None
            if producto.unidad_venta_id:
                print("Obteniendo unidad de medida para ID: ", producto.unidad_venta_id)
                unidad_medida = uow.unidad_medida.get_by_id(producto.unidad_venta_id)
                print("Unidad de medida obtenida: ", unidad_medida)

            stock_fabricable = self.calcular_stock_por_ingredientes(uow, producto_id)
            stock_efectivo = stock_fabricable if stock_fabricable is not None else producto.stock
            producto_dict = producto.model_dump()
            producto_dict.pop('stock', None) 
            result = ProductoReadFull(
                **producto_dict,
                stock=stock_efectivo,
                unidad_medida=unidad_medida.model_dump() if unidad_medida else None,
                ingredientes=response_ingredientes,
                categorias=response_categorias
            )

        return result

    def deactive(self, producto_id: int) -> Optional[Producto]:
        with ProductoUnitOfWork(self._session) as uow:
            producto = self._get_or_404(uow, producto_id)
            producto.activo = False
            producto.deleted_at = datetime.now(timezone.utc).isoformat()
            uow.productos.add(producto)
        return producto

    def agregar_categoria_a_producto(self, producto_id: int, categoria_id: int, es_principal: bool) -> ProductoRead:
        with ProductoUnitOfWork(self._session) as uow:
            self._assert_link_not_exists(uow, producto_id, categoria_id)        
            self._get_categoria_or_404(uow, categoria_id)
            producto = self._get_full_or_404(uow, producto_id)

            uow.productos.link_categoria(producto_id, categoria_id, es_principal)
            result = ProductoRead.model_validate(producto)
        return result
    
    # ─── Nuevos métodos para manejo de ingredientes ─────────────────────────
    
    def agregar_ingrediente_a_producto(self, producto_id: int, ingrediente_id: int, es_removible: bool, cantidad: Decimal) -> ProductoRead:
        with ProductoUnitOfWork(self._session) as uow:
            self._assert_ingrediente_link_not_exists(uow, producto_id, ingrediente_id)
            self._get_ingrediente_or_404(uow, ingrediente_id)
            producto = self._get_full_or_404(uow, producto_id)
            
            uow.productos.link_ingrediente(producto_id, ingrediente_id, es_removible, cantidad)
            result = ProductoRead.model_validate(producto)
        return result
    
    def remover_ingrediente_de_producto(self, producto_id: int, ingrediente_id: int) -> ProductoRead:
        with ProductoUnitOfWork(self._session) as uow:
            producto = self._get_or_404(uow, producto_id)
            ingrediente = self._get_ingrediente_or_404(uow, ingrediente_id)
            
            # Verificar si la relación existe
            link = uow.productos.get_ingrediente_link(producto_id, ingrediente_id)
            if not link:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"El producto {producto_id} no tiene asignado el ingrediente {ingrediente_id}"
                )
            
            uow.productos.unlink_ingrediente(producto_id, ingrediente_id)
            result = ProductoRead.model_validate(producto)
        return result
    
    def actualizar_ingrediente_removible(self, producto_id: int, ingrediente_id: int, es_removible: bool) -> ProductoRead:
        with ProductoUnitOfWork(self._session) as uow:
            producto = self._get_or_404(uow, producto_id)
            
            # Verificar que la relación existe
            link = uow.productos.get_ingrediente_link(producto_id, ingrediente_id)
            if not link:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"El producto {producto_id} no tiene asignado el ingrediente {ingrediente_id}"
                )
            
            # Actualizar la propiedad es_removible
            uow.productos.update_ingrediente_removible(producto_id, ingrediente_id, es_removible)
            result = ProductoRead.model_validate(producto)
        return result
    
    def obtener_estado_stock(self, producto_id: int) -> Optional[dict]:
        with ProductoUnitOfWork(self._session) as uow:
            producto = self._get_or_404(uow, producto_id)
            stock_fabricable = self.calcular_stock_por_ingredientes(uow, producto_id)
            stock_efectivo= stock_fabricable if stock_fabricable is not None else producto.stock
            alerta_stock = stock_efectivo < producto.stock_minimo
            result = {
                "stock": stock_efectivo,
                "bajo_stock_minimo": alerta_stock,
                "activo": producto.activo,
                "disponible": producto.disponible
            }
        return result
    
    def remover_categoria_de_producto(self, producto_id: int, categoria_id: int) -> ProductoRead:
        with ProductoUnitOfWork(self._session) as uow:
            producto = self._get_or_404(uow, producto_id)
            categoria = self._get_categoria_or_404(uow, categoria_id)

            if categoria in producto.categorias:
                uow.productos.unlink_categoria(producto_id, categoria_id)
            
            result = ProductoRead.model_validate(producto)
        return result
    
    def actualizar(self, producto_id: int, data: ProductoUpdate) -> ProductoRead:
        with ProductoUnitOfWork(self._session) as uow:
            producto = self._get_or_404(uow, producto_id)

            update_data = data.dict(exclude_unset=True, exclude={'ingredientes', 'categorias_ids'})
            for field, value in update_data.items():
                setattr(producto, field, value)

            if data.ingredientes is not None:
                for link in uow.productos.get_all_ingrediente_links(producto_id):
                    uow.productos.unlink_ingrediente(producto_id, link.ingrediente_id)
                for ing in data.ingredientes:
                    uow.productos.link_ingrediente(producto_id, ing.ingrediente_id, ing.es_removible, ing.cantidad)

            if data.categorias_ids is not None:
                for categoria in producto.categorias:
                    uow.productos.unlink_categoria(producto_id, categoria.id)
                
                for cat_id in data.categorias_ids:
                    self._get_categoria_or_404(uow, cat_id) 
                    uow.productos.link_categoria(producto_id, cat_id, es_principal=False)

            uow.productos.add(producto)
            result = ProductoRead.model_validate(producto)
        return result
    
    def reactivar(self, producto_id: int) -> Optional[Producto]:
        with ProductoUnitOfWork(self._session) as uow:
            producto = self._get_or_404(uow, producto_id)
            producto.activo = True
            producto.deleted_at = None  # Limpiar la fecha de eliminación
            producto.updated_at = datetime.now(timezone.utc)
            uow.productos.add(producto)
        return producto
    
    def obtener_producto_por_categoria(self, categoria_id: int) -> ProductoPaginadoResponse:
        with ProductoUnitOfWork(self._session) as uow:
            categoria = self._get_categoria_or_404(uow, categoria_id)
            productos = uow.productos.get_by_categoria(categoria_id)
            result = [ProductoRead.model_validate(p) for p in productos]
        return ProductoPaginadoResponse(
            items=result,
            total=len(result)
        )