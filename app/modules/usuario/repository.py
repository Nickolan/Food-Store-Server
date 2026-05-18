from typing import Optional, List
from sqlmodel import select
from app.core.repository import BaseRepository
from app.modules.usuario.models import Usuario, Rol, UsuarioRol


class UsuarioRepository(BaseRepository[Usuario]):

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


class RolRepository(BaseRepository[Rol]):

    def __init__(self, session) -> None:
        super().__init__(session, Rol)

    def get_by_codigo(self, codigo: str) -> Optional[Rol]:
        return self.session.exec(
            select(Rol).where(Rol.codigo == codigo)
        ).first()

    def get_all_roles(self) -> List[Rol]:
        return list(self.session.exec(select(Rol)).all())


class UsuarioRolRepository(BaseRepository[UsuarioRol]):

    def __init__(self, session) -> None:
        super().__init__(session, UsuarioRol)

    def get_asignacion(self, usuario_id: int, rol_codigo: str) -> Optional[UsuarioRol]:
        stmt = select(UsuarioRol).where(
            UsuarioRol.usuario_id == usuario_id,
            UsuarioRol.rol_codigo == rol_codigo
        )
        return self.session.exec(stmt).first()

    def get_roles_por_usuario(self, usuario_id: int) -> List[UsuarioRol]:
        stmt = select(UsuarioRol).where(UsuarioRol.usuario_id == usuario_id)
        return list(self.session.exec(stmt).all())
