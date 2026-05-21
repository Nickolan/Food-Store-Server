from sqlmodel import select

from app.core.repository import BaseRepository
from .model import HistorialEstadoPedido

class HistorialEstadoPedidoRepository(BaseRepository):
    def __init__(self,session):
        super().__init__(session,HistorialEstadoPedido)
    def obtener_por_pedido(self,id:int):
        resultado=select(HistorialEstadoPedido).where(HistorialEstadoPedido.pedido_id == id).order_by(HistorialEstadoPedido.created_at.asc())
        return self.session.exec(resultado).all()