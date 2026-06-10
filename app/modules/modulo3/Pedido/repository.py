from sqlmodel import select

from app.core.repository import BaseRepository
from .model import Pedido

class PedidoRepository(BaseRepository):
    def __init__(self,session):
        super().__init__(session,Pedido)
    def obtener_por_usuario(self,usuario_id:int, skip:int, limit:int):
        query=select(Pedido).where(Pedido.usuario_id==usuario_id).order_by(Pedido.created_at.desc()).offset(skip).limit(limit)
        return self.session.exec(query).all()
        
    def get_all(self, skip: int = 0, limit: int = 100):
        query=select(Pedido).order_by(Pedido.created_at.desc()).offset(skip).limit(limit)
        return self.session.exec(query).all()