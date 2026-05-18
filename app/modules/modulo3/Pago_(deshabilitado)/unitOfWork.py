from app.core.repository import BaseUnitOfWork
from app.modules.modulo3.HistorialEstadoPedido.repository import HistorialEstadoPedidoRepository
from app.modules.modulo3.Pedido.repository import PedidoRepository
from .repository import PagoRepository


class PagoUnitOfWork(BaseUnitOfWork):
    def __enter__(self):
        super().__enter__()
        self.pagos=PagoRepository(self._session)
        self.pedidos = PedidoRepository(self._session)
        self.historiales = HistorialEstadoPedidoRepository(self._session)
        return self