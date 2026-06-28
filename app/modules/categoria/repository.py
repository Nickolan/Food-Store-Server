from app.core.repository import BaseRepository
from sqlalchemy.orm import selectinload
from sqlmodel import select
from app.modules.categoria.models import Categoria
from typing import List, Optional

class CategoriaRepository(BaseRepository[Categoria]):
    """
    
    Repositorio de Categorias
    
    """

    def __init__(self, session) -> None:
        super().__init__(session, Categoria)

    def get_paginado(self, offset: int = 0, limit: int = 20, nombre: Optional[str] = None, activo: Optional[bool] = None, parent_id: Optional[int] = None, solo_raiz: bool = False) -> list[Categoria]:
        stmt = select(Categoria)
        if activo is True:
            stmt = stmt.where(Categoria.deleted_at == None)
        elif activo is False:
            stmt = stmt.where(Categoria.deleted_at != None)
        else:
            stmt = stmt.where(Categoria.deleted_at == None)
        if nombre:
            stmt = stmt.where(Categoria.nombre.ilike(f"%{nombre}%"))
        if solo_raiz:
            stmt = stmt.where(Categoria.parent_id == None)
        elif parent_id is not None:
            stmt = stmt.where(Categoria.parent_id == parent_id)
        return list(self.session.exec(stmt.offset(offset).limit(limit)).all())

    def get_subcategorias(self, categoria_id: int) -> list[Categoria]:
        stmt = select(Categoria).where(Categoria.parent_id == categoria_id).where(Categoria.deleted_at == None)
        return list(self.session.exec(stmt).all())

    def count(self, nombre: Optional[str] = None, activo: Optional[bool] = None, parent_id: Optional[int] = None, solo_raiz: bool = False) -> int:
        stmt = select(Categoria)
        if activo is True:
            stmt = stmt.where(Categoria.deleted_at == None)
        elif activo is False:
            stmt = stmt.where(Categoria.deleted_at != None)
        else:
            stmt = stmt.where(Categoria.deleted_at == None)
        if nombre:
            stmt = stmt.where(Categoria.nombre.ilike(f"%{nombre}%"))
        if solo_raiz:
            stmt = stmt.where(Categoria.parent_id == None)
        elif parent_id is not None:
            stmt = stmt.where(Categoria.parent_id == parent_id)
        return len(self.session.exec(stmt).all())
    
    # def get_by_descripcion(self, descripcion: str) -> Categoria | None:
    #     return self.session.exec(
    #         select(Categoria).where(Categoria.descripcion == descripcion)
    #     ).first()
    
    # def get_by_codigo(self, codigo: str) -> Categoria | None:
    #     return self.session.exec(
    #         select(Categoria).where(Categoria.codigo == codigo)
    #     ).first()
    
    def get_by_nombre(self, nombre: str) -> Categoria | None:
        return self.session.exec(
            select(Categoria).where(Categoria.nombre == nombre)
        ).first()