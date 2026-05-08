from datetime import datetime

from fastapi import HTTPException, status
from typing import List, Optional, Tuple
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select, func

from .models import Categoria
from .schemas import CategoriaCreate, CategoriaUpdate, CategoriaRead, CategoriaPaginadoResponse, CategoriaReadFull
from app.modules.categoria.unit_of_work import CategoriaUnitOfWork
from app.modules.producto.schemas import ProductoRead

class CategoriaService:
    def __init__(self, session: Session) -> None:
        self._session = session

    # Helpers

    def _get_or_404(self, uow: CategoriaUnitOfWork, categoria_id: int) -> Categoria:
        categoria = uow.categorias.get_by_id(categoria_id)
        if not categoria:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categoria con id={categoria_id} no encontrada",
            )
        return categoria
        
    def _assert_nombre_unique(self, uow: CategoriaUnitOfWork, nombre: str, exclude_id: Optional[int] = None) -> Optional[Categoria]:
        existing = uow.categorias.get_by_nombre(nombre)
        if existing and existing.id != exclude_id:
            if existing.deleted_at is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya existe una categoria activa con nombre='{nombre}'",
                )
            return existing
        return None
        
    # Casos de Uso
        
    def crear_categoria(self, data: CategoriaCreate) -> CategoriaRead:
        with CategoriaUnitOfWork(self._session) as uow:
            existing = self._assert_nombre_unique(uow, data.nombre)
            if existing and existing.deleted_at is not None:
                # Si existe pero está eliminada lógicamente, la restauramos
                existing.deleted_at = None
                existing.activo = data.activo
                existing.descripcion = data.descripcion
                if data.imagen_url is not None:
                    existing.imagen_url = data.imagen_url
                if data.parent_id is not None:
                    existing.parent_id = data.parent_id
                existing.updated_at = datetime.utcnow().isoformat()
                uow.categorias.add(existing)
                result = CategoriaRead.model_validate(existing)
            else:
                nueva = Categoria.model_validate(data)
                uow.categorias.add(nueva)
                result = CategoriaRead.model_validate(nueva)
        return result
    
    def obtener_todas(self, offset: int = 0, limit: int = 20, nombre: Optional[str] = None) -> CategoriaPaginadoResponse:
        with CategoriaUnitOfWork(self._session) as uow:
            categorias = uow.categorias.get_paginado(offset=offset, limit=limit, nombre=nombre)
            total = uow.categorias.count()
            items = [CategoriaRead.model_validate(c) for c in categorias]
        return CategoriaPaginadoResponse(total=total, items=items)
    
    def obtener_por_id(self, categoria_id: int) -> CategoriaReadFull:
        with CategoriaUnitOfWork(self._session) as uow:
            categoria = self._get_or_404(uow, categoria_id)
            productos = uow.productos.get_by_categoria(categoria_id)
            sub_categorias = uow.categorias.get_subcategorias(categoria_id)

            categoria_data = categoria.model_dump()
            productos_data = [ProductoRead.model_validate(p) for p in productos]
            subcategorias_data = [CategoriaRead.model_validate(c) for c in sub_categorias]
            datos_completos = {
                **categoria_data,
                "productos": productos_data,
                "subcategorias": subcategorias_data
            }
            result = CategoriaReadFull.model_validate(datos_completos)
        return result
    
    def actualizar_total(self, categoria_id: int, data: CategoriaUpdate) -> Optional[Categoria]:
        with CategoriaUnitOfWork(self._session) as uow:
            categoria = self._get_or_404(uow, categoria_id)
            if data.nombre and data.nombre != categoria.nombre:
                existing = self._assert_nombre_unique(uow, data.nombre, exclude_id=categoria_id)
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"El nombre '{data.nombre}' ya pertenece a otra categoría (posiblemente eliminada).",
                    )
            categoria_data = data.model_dump(exclude_unset=True)
            for key, value in categoria_data.items():
                setattr(categoria, key, value)

            categoria.updated_at = datetime.utcnow().isoformat()
            uow.categorias.add(categoria)
        return categoria
    
    def agregar_categoria_padre(self, categoria_id: int, parent_id: int) -> Optional[Categoria]:
        with CategoriaUnitOfWork(self._session) as uow:
            categoria = self._get_or_404(uow, categoria_id)
            parent = self._get_or_404(uow, parent_id)
            if categoria_id == parent_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Una categoría no puede ser su propia padre",
                )
            
            if categoria.activo == False or parent.activo == False:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se puede asignar una subcategoría a una categoría inactiva o asignar una categoría inactiva como padre",
                )
            categoria.parent_id = parent_id
            categoria.updated_at = datetime.utcnow().isoformat()
            uow.categorias.add(categoria)
        return categoria
    
    def desactivar(self, categoria_id: int) -> Optional[Categoria]:
        with CategoriaUnitOfWork(self._session) as uow:
            # First ensure the category exists
            categoria = self._get_or_404(uow, categoria_id)
            
            def _desactivar_recursivo(cat_id: int):
                cat = uow.categorias.get_by_id(cat_id)
                if not cat or cat.deleted_at:
                    return
                cat.activo = False
                cat.deleted_at = datetime.utcnow().isoformat()
                uow.categorias.add(cat)
                
                subs = uow.categorias.get_subcategorias(cat_id)
                for sub in subs:
                    if sub.id:
                        _desactivar_recursivo(sub.id)
                        
            _desactivar_recursivo(categoria_id)
            
        return categoria