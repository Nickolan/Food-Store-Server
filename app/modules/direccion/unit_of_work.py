from sqlmodel import Session
from app.core.unit_of_work import UnitOfWork
from app.modules.direccion.repository import DireccionRepository


class DireccionUoW(UnitOfWork):
    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self.direcciones = DireccionRepository(session)
