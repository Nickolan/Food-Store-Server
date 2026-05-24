from sqlmodel import Session
from app.modules.unidad_medida.repository import UnidadMedidaRepository
from app.core.unit_of_work import UnitOfWork
from app.modules.producto.repository import ProductoRepository
from app.modules.categoria.repository import CategoriaRepository
from app.modules.ingrediente.repository import IngredienteRepository

class ProductoUnitOfWork(UnitOfWork):
    def __init__(self, session) -> None:
        super().__init__(session)
        self.productos = ProductoRepository(session)
        self.categorias = CategoriaRepository(session)
        self.ingredientes = IngredienteRepository(session)
        self.unidad_medida = UnidadMedidaRepository(session)

    def flush(self) -> None:
        self._session.flush()