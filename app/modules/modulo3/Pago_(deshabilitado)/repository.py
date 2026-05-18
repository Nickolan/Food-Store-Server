from app.core.repository import BaseRepository
from .model import Pago

class PagoRepository(BaseRepository):
    def __init__(self,session):
        super().__init__(session,Pago)