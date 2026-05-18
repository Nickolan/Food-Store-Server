from app.core.unit_of_work import UnitOfWork
from .repository import EstadoPedidoRepository


class EstadoPedidoUnitOfWork(UnitOfWork):
    def __enter__(self):
        super().__enter__()
        self.estados=EstadoPedidoRepository(self._session)
        return self