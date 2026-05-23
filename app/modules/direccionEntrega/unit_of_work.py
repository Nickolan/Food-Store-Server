from sqlmodel import Session
from app.core.unit_of_work import UnitOfWork
from app.modules.direccionEntrega.repository import DireccionEntregaRepository


class DireccionUoW(UnitOfWork):
    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self.direcciones = DireccionEntregaRepository(session)
