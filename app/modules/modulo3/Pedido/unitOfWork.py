from app.core.unit_of_work import UnitOfWork
from app.modules.direccion.repository import DireccionRepository
from app.modules.producto.repository import ProductoRepository
from app.modules.usuario.repository import UsuarioRepository
from app.modules.modulo3.EstadoPedido.repository import EstadoPedidoRepository
from app.modules.modulo3.HistorialEstadoPedido.repository import HistorialEstadoPedidoRepository
from .repository import PedidoRepository
from ..Formapago.repository import FormaPagoRepository

class PedidoUnitOfWork(UnitOfWork):
    def __enter__(self):
        super().__enter__()
        self.pedidos=PedidoRepository(self._session)
        self.estados=EstadoPedidoRepository(self._session)
        self.formapago=FormaPagoRepository(self._session)
        self.usuarios = UsuarioRepository(self._session) 
        self.historiales=HistorialEstadoPedidoRepository(self._session)
        self.productos = ProductoRepository(self._session)
        self.direcciones = DireccionRepository(self._session)
        return self