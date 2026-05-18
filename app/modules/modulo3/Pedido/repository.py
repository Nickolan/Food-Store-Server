from sqlmodel import select

from app.core.repository import BaseRepository
from .model import Pedido

class PedidoRepository(BaseRepository):
    def __init__(self,session):
        super().__init__(session,Pedido)
    def obtener_por_usuario(self,usuario_id:int, skip:int, limit:int):
        query=select(Pedido).where(Pedido.usuario_id==usuario_id).offset(skip).limit(limit)
        return self.session.exec(query).all()