from typing import Optional, List
from sqlmodel import Session, select, update
from app.core.repository import BaseRepository
from app.modules.direccion.models import Direccion

class DireccionRepository(BaseRepository[Direccion]):    
    """
    Repositorio de Direcciones

    """

    def __init__(self, session: Session) -> None:
        super().__init__(session, Direccion)
    
    def get_by_usuario(self, usuario_id: int, direccion_id: int) -> Optional[Direccion]:
        return self.session.exec(
            select(Direccion).where(
                Direccion.id == direccion_id,
                Direccion.usuario_id == usuario_id,
                Direccion.deleted_at.is_(None)
            )
        ).first()
    
    def get_all_by_usuario(self, usuario_id: int) -> List[Direccion]:
        return list(
            self.session.exec(
                select(Direccion)
                .where(
                    Direccion.usuario_id == usuario_id,
                    Direccion.deleted_at.is_(None)
                )
                .order_by(Direccion.es_principal.desc(), Direccion.created_at.desc())
            ).all()
        )
    
    def get_principal_by_usuario(self, usuario_id: int) -> Optional[Direccion]:
        return self.session.exec(
            select(Direccion)
            .where(
                Direccion.usuario_id == usuario_id,
                Direccion.es_principal == True,
                Direccion.deleted_at.is_(None)
            )
        ).first()
    
    def reset_principal_flag(self, usuario_id: int) -> None:
        self.session.exec(
            update(Direccion)
            .where(
                Direccion.usuario_id == usuario_id,
                Direccion.es_principal == True,
                Direccion.deleted_at.is_(None)
            )
            .values(es_principal=False)
        )
        self.session.flush()
    
    def count_by_usuario(self, usuario_id: int) -> int:
        return len(
            self.session.exec(
                select(Direccion).where(
                    Direccion.usuario_id == usuario_id,
                    Direccion.deleted_at.is_(None)
                )
            ).all()
        )