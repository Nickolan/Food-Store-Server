from fastapi import Depends
from sqlmodel import Session
from app.core.database import get_session
from app.core.unit_of_work import UnitOfWork
from app.modules.usuario.repository import (
    UsuarioRepository, 
    RolRepository, 
    UsuarioRolRepository
)

class UsuarioUnitOfWork(UnitOfWork):
    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self.usuarios = UsuarioRepository(session)
        self.roles = RolRepository(session)
        self.usuario_roles = UsuarioRolRepository(session)

    def flush(self) -> None:
            self._session.flush()

def get_uow(session: Session = Depends(get_session)) -> UsuarioUnitOfWork:
    """Dependencia FastAPI: provee un UnitOfWork por request."""
    return UsuarioUnitOfWork(session)
