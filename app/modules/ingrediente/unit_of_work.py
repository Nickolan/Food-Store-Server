from sqlmodel import Session
from app.core.unit_of_work import UnitOfWork
from app.modules.ingrediente.repository import IngredienteRepository
from app.modules.producto.repository import ProductoRepository

class IngredienteUnitOfWork(UnitOfWork):
    def __init__(self, session) -> None:
        super().__init__(session)
        self.ingredientes = IngredienteRepository(session)
        self.productos = ProductoRepository(session)