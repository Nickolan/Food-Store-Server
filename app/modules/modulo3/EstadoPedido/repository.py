from app.core.repository import BaseRepository
from .model import EstadoPedido

class EstadoPedidoRepository(BaseRepository):
    def __init__(self,session):
        super().__init__(session,EstadoPedido)