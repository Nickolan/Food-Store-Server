from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from app.core.repository import BaseRepository
from app.modules.producto.models import Producto, ProductoCategoriaLink
from app.modules.categoria.models import Categoria
from app.modules.ingrediente.models import IngredienteProductoLink
from decimal import Decimal

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
    
    def get_paginado(self, offset: int = 0, limit: int = 20, nombre: str | None = None, activo: bool | None = None) -> list[Producto]:
        stmt = select(Producto)
        if nombre:
            stmt = stmt.where(Producto.nombre.ilike(f"%{nombre}%"))
        if activo is not None:
            stmt = stmt.where(Producto.activo == activo)
        return list(
            self.session.exec(
                stmt.offset(offset).limit(limit)
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
            .options(selectinload(Producto.unidad_medida))
        ).first()
    
    def count(self, nombre: str | None = None, activo: bool | None = None) -> int:
        stmt = select(Producto)
        if nombre:
            stmt = stmt.where(Producto.nombre.ilike(f"%{nombre}%"))
        if activo is not None:
            stmt = stmt.where(Producto.activo == activo)
        return len(self.session.exec(stmt).all())


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
        self.session.flush()
        self.session.refresh(link)
        return link
    
    def unlink_categoria(self, producto_id: int, categoria_id: int) -> None:
        link = self.get_link(producto_id, categoria_id)
        if link:
            self.session.delete(link)
            self.session.flush()

    # ─── Ingrediente link helpers ────────────────────────────────────────

    def get_ingrediente_link(self, producto_id: int, ingrediente_id: int) -> IngredienteProductoLink | None:
        return self.session.exec(
            select(IngredienteProductoLink).where(
                IngredienteProductoLink.producto_id == producto_id,
                IngredienteProductoLink.ingrediente_id == ingrediente_id
            )
        ).first()

    def get_all_ingrediente_links(self, producto_id: int) -> list[IngredienteProductoLink]:
        return list(self.session.exec(
            select(IngredienteProductoLink).where(
                IngredienteProductoLink.producto_id == producto_id
            )
        ).all())

    def link_ingrediente(self, producto_id: int, ingrediente_id: int, es_removible: bool, cantidad: Decimal) -> IngredienteProductoLink:
        link = IngredienteProductoLink(
            producto_id=producto_id,
            ingrediente_id=ingrediente_id,
            es_removible=es_removible,
            cantidad=cantidad,
        )
        self.session.add(link)
        self.session.flush()
        self.session.refresh(link)
        return link

    def unlink_ingrediente(self, producto_id: int, ingrediente_id: int) -> None:
        link = self.get_ingrediente_link(producto_id, ingrediente_id)
        if link:
            self.session.delete(link)
            self.session.flush()

    def update_ingrediente_removible(self, producto_id: int, ingrediente_id: int, es_removible: bool) -> None:
        link = self.get_ingrediente_link(producto_id, ingrediente_id)
        if link:
            link.es_removible = es_removible
            self.session.add(link)
            self.session.flush()
    def get_ingredientes_removibles(self, producto_id: int) -> list[int]:
        return list(self.session.exec(
            select(IngredienteProductoLink.ingrediente_id).where(
                IngredienteProductoLink.producto_id == producto_id,
                IngredienteProductoLink.es_removible == True
            )
        ).all())