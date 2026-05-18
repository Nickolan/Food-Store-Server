from app.core.unit_of_work import UnitOfWork
from app.modules.modulo3.EstadoPedido.repository import EstadoPedidoRepository
from app.modules.modulo3.Pedido.repository import PedidoRepository
from .repository import HistorialEstadoPedidoRepository


class HistorialEstadoPedidoUnitOfWork(UnitOfWork):
    def __enter__(self):
        super().__enter__()
        self.historiales=HistorialEstadoPedidoRepository(self._session)
        self.estados = EstadoPedidoRepository(self._session)
        self.pedidos = PedidoRepository(self._session)
        return self