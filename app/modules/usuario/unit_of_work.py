from sqlmodel import Session
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


def get_uow() -> UsuarioUnitOfWork:
    return UsuarioUnitOfWork()