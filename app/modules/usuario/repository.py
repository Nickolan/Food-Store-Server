from typing import Optional
from sqlmodel import select
from app.core.repository import BaseRepository
from app.modules.usuario.models import Usuario


class UsuarioRepository(BaseRepository[Usuario]):
    """
    Repositorio de Usuarios
    """

    def __init__(self, session) -> None:
        super().__init__(session, Usuario)

    def get_by_email(self, email: str) -> Optional[Usuario]:
        return self.session.exec(
            select(Usuario).where(Usuario.email == email)
        ).first()

    def get_activos(self, offset: int = 0, limit: int = 20) -> list[Usuario]:
        stmt = (
            select(Usuario)
            .where(Usuario.deleted_at == None)
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(stmt).all())

    def count_activos(self) -> int:
        return len(
            self.session.exec(
                select(Usuario).where(Usuario.deleted_at == None)
            ).all()
        )
