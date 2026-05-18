from app.core.repository import BaseRepository
from .model import FormaPago

class FormaPagoRepository(BaseRepository):
    def __init__(self,session):
        super().__init__(session,FormaPago)