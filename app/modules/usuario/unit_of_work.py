from sqlmodel import Session
from app.core.unit_of_work import UnitOfWork
from app.modules.usuario.repository import UsuarioRepository


class UsuarioUnitOfWork(UnitOfWork):
    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self.usuarios = UsuarioRepository(session)

def get_uow() -> UsuarioUnitOfWork:
    """Dependencia FastAPI: provee un UnitOfWork por request."""
    return UsuarioUnitOfWork()