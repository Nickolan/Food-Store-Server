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

    def get_paginado(self, offset: int = 0, limit: int = 20, nombre: Optional[str] = None) -> list[Categoria]:
        stmt = select(Categoria)
        if nombre:
            stmt = stmt.where(Categoria.nombre.ilike(f"%{nombre}%"))
        return list(
            self.session.exec(
                stmt
                .offset(offset)
                .limit(limit)
            ).all()
        )
    

    # Traer subcategorias de una categoria
    def get_subcategorias(self, categoria_id: int) -> list[Categoria]:
        stmt = select(Categoria).where(Categoria.parent_id == categoria_id)
        return list(self.session.exec(stmt).all())
    
    def count(self) -> int:
        return len(self.session.exec(select(Categoria)).all())
    
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