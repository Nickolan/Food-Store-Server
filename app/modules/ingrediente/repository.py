from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from app.core.repository import BaseRepository
from app.modules.ingrediente.models import Ingrediente, IngredienteProductoLink
from app.modules.producto.models import Producto

class IngredienteRepository(BaseRepository[Ingrediente]):
    """
    Repositorio de Ingredientes

    """

    def __init__(self, session) -> None:
        super().__init__(session, Ingrediente)

    def get_by_nombre(self, nombre: str) -> Ingrediente | None:
        return self.session.exec(
            select(Ingrediente).where(Ingrediente.nombre == nombre)
        ).first()
    
    def get_paginado(self, offset: int = 0, limit: int = 20) -> list[Ingrediente]:
        return list(
            self.session.exec(
                select(Ingrediente)
                .offset(offset)
                .limit(limit)
            ).all()
        )
    
    def get_with_productos(self, ingrediente_id: int) -> Ingrediente | None:
        return self.session.exec(
            select(Ingrediente)
            .where(Ingrediente.id == ingrediente_id)
            .options(selectinload(Ingrediente.productos))
        ).first()
    
    def count(self) -> int:
        return len(self.session.exec(select(Ingrediente)).all())
    
    def get_link(self, ingrediente_id: int, producto_id: int) -> IngredienteProductoLink | None:
        return self.session.exec(
            select(IngredienteProductoLink)
            .where(
                IngredienteProductoLink.ingrediente_id == ingrediente_id,
                IngredienteProductoLink.producto_id == producto_id
            )
        ).first()
    
    def link_producto(self, ingrediente_id: int, producto_id: int, es_removible: bool) -> IngredienteProductoLink:
        link = IngredienteProductoLink(ingrediente_id=ingrediente_id, producto_id=producto_id, es_removible=es_removible)
        self.session.add(link)
        self.session.commit()
        return link
    
    def unlink_producto(self, ingrediente_id: int, producto_id: int) -> None:
        link = self.get_link(ingrediente_id, producto_id)
        if link:
            self.session.delete(link)
            self.session.commit()