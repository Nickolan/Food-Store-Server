from typing import Optional, List
from sqlmodel import Session, select, update
from app.core.repository import BaseRepository
from app.modules.direccionEntrega.models import DireccionEntrega

class DireccionEntregaRepository(BaseRepository[DireccionEntrega]):    
    """
    Repositorio de Direcciones

    """

    def __init__(self, session: Session) -> None:
        super().__init__(session, DireccionEntrega)
    
    def get_by_usuario(self, usuario_id: int, direccion_id: int) -> Optional[DireccionEntrega]:
        return self.session.exec(
            select(DireccionEntrega).where(
                DireccionEntrega.id == direccion_id,
                DireccionEntrega.usuario_id == usuario_id,
                DireccionEntrega.deleted_at.is_(None)
            )
        ).first()
    
    def get_all_by_usuario(self, usuario_id: int) -> List[DireccionEntrega]:
        return list(
            self.session.exec(
                select(DireccionEntrega)
                .where(
                    DireccionEntrega.usuario_id == usuario_id,
                    DireccionEntrega.deleted_at.is_(None)
                )
                .order_by(DireccionEntrega.es_principal.desc(), DireccionEntrega.created_at.desc())
            ).all()
        )
    
    def get_principal_by_usuario(self, usuario_id: int) -> Optional[DireccionEntrega]:
        return self.session.exec(
            select(DireccionEntrega)
            .where(
                DireccionEntrega.usuario_id == usuario_id,
                DireccionEntrega.es_principal == True,
                DireccionEntrega.deleted_at.is_(None)
            )
        ).first()
    
    def reset_principal_flag(self, usuario_id: int) -> None:
        self.session.exec(
            update(DireccionEntrega)
            .where(
                DireccionEntrega.usuario_id == usuario_id,
                DireccionEntrega.es_principal == True,
                DireccionEntrega.deleted_at.is_(None)
            )
            .values(es_principal=False)
        )
        self.session.flush()
    
    def count_by_usuario(self, usuario_id: int) -> int:
        return len(
            self.session.exec(
                select(DireccionEntrega).where(
                    DireccionEntrega.usuario_id == usuario_id,
                    DireccionEntrega.deleted_at.is_(None)
                )
            ).all()
        )