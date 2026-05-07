from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from app.core.repository import BaseRepository
from app.modules.producto.models import Producto, ProductoCategoriaLink
from app.modules.categoria.models import Categoria

class ProductoRepository(BaseRepository[Producto]):
    """
    Repositorio de Productos

    """

    def __init__(self, session) -> None:
        super().__init__(session, Producto)

    def get_by_nombre(self, nombre: str) -> Producto | None:
        return self.session.exec(
            select(Producto).where(Producto.nombre == nombre)
        )
    
    def get_paginado(self, offset: int = 0, limit: int = 20) -> list[Producto]:
        return list(
            self.session.exec(
                select(Producto)
                .where(Producto.activo == True)
                .offset(offset)
                .limit(limit)
            ).all()
        )
    
    def get_with_categorias(self, producto_id: int) -> Producto | None:
        return self.session.exec(
            select(Producto)
            .where(Producto.id == producto_id)
            .options(selectinload(Producto.categorias))
        ).first()
    
    def get_full_by_id(self, producto_id: int) -> Producto | None:
        return self.session.exec(
            select(Producto)
            .where(Producto.id == producto_id)
            .options(selectinload(Producto.categorias))
            .options(selectinload(Producto.ingredientes))
        ).first()
    
    def count(self) -> int:
        return len(self.session.exec(select(Producto)).all())


    def get_by_categoria(self, categoria_id: int) -> list[Producto]:
        return list(
            self.session.exec(
                select(Producto)
                .join(ProductoCategoriaLink)
                .where(ProductoCategoriaLink.categoria_id == categoria_id)
            ).all()
        )
    
    def get_link(self, producto_id: int, categoria_id: int) -> ProductoCategoriaLink | None:
        return self.session.exec(
            select(ProductoCategoriaLink)
            .where(
                ProductoCategoriaLink.producto_id == producto_id,
                ProductoCategoriaLink.categoria_id == categoria_id
            )
        ).first()
    
    def link_categoria(self, producto_id: int, categoria_id: int, es_principal: bool) -> ProductoCategoriaLink:
        link = ProductoCategoriaLink(producto_id=producto_id, categoria_id=categoria_id, es_principal=es_principal)
        self.session.add(link)
        self.session.commit()
        self.session.refresh(link)
        return link
    
    def unlink_categoria(self, producto_id: int, categoria_id: int) -> None:
        link = self.get_link(producto_id, categoria_id)
        if link:
            self.session.delete(link)
            self.session.commit()