from fastapi import Depends
from sqlmodel import Session
from app.core.database import get_session
from app.core.unit_of_work import UnitOfWork
from app.modules.unidad_medida.repository import UnidadMedidaRepository

class UnidadMedidaUnitOfWork(UnitOfWork):
    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self.unidades_medida = UnidadMedidaRepository(session)

    def flush(self) -> None:
        self._session.flush()

def get_uow(session: Session = Depends(get_session)) -> UnidadMedidaUnitOfWork:
    return UnidadMedidaUnitOfWork(session)
