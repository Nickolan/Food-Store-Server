from app.core.unit_of_work import UnitOfWork
from app.modules.modulo3.HistorialEstadoPedido.repository import HistorialEstadoPedidoRepository
from app.modules.modulo3.Pedido.repository import PedidoRepository
from app.modules.modulo3.EstadoPedido.repository import EstadoPedidoRepository
from .repository import PagoRepository


class PagoUnitOfWork(UnitOfWork):
    def __enter__(self):
        super().__enter__()
        self.pagos=PagoRepository(self._session)
        self.pedidos = PedidoRepository(self._session)
        self.historiales = HistorialEstadoPedidoRepository(self._session)
        self.estados = EstadoPedidoRepository(self._session)
        return self