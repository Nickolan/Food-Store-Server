from sqlmodel import select

from app.core.repository import BaseRepository
from .model import EstadoPedido

class EstadoPedidoRepository(BaseRepository):
    def __init__(self,session):
        super().__init__(session,EstadoPedido)
    def get_by_codigo(self, codigo: str):
        statement = select(EstadoPedido).where(EstadoPedido.codigo == codigo)
        return self.session.exec(statement).first()