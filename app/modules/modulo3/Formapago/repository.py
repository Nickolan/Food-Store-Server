from sqlmodel import select

from app.core.repository import BaseRepository
from .model import FormaPago

class FormaPagoRepository(BaseRepository):
    def __init__(self,session):
        super().__init__(session,FormaPago)
    def get_by_codigo(self, codigo: str):
        statement = select(FormaPago).where(FormaPago.codigo == codigo)
        return self.session.exec(statement).first()