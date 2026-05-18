from typing import Optional, List
from sqlmodel import Session, select, update
from app.modules.direccion.models import Direccion

class DireccionRepository:
    """
    Repositorio de Direcciones

    """
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, direccion: Direccion) -> Direccion:
        self.session.add(direccion)
        self.session.flush()
        self.session.refresh(direccion)
        return direccion
    
    def get_by_id(self, direccion_id: int, usuario_id: int) -> Optional[Direccion]:
        statement = select(Direccion).where(
            Direccion.id == direccion_id,
            Direccion.usuario_id == usuario_id
        )
        return self.session.exec(statement).first()
    
    def get_all_by_usuario(self, usuario_id: int) -> List[Direccion]:
        statement = select(Direccion).where(
            Direccion.usuario_id == usuario_id
        ).order_by(Direccion.es_principal.desc(), Direccion.created_at.desc())
        return self.session.exec(statement).all()
    
    def get_principal_by_usuario(self, usuario_id: int) -> Optional[Direccion]:
        statement = select(Direccion).where(
            Direccion.usuario_id == usuario_id,
            Direccion.es_principal == True
        )
        return self.session.exec(statement).first()
    
    def update(self, direccion: Direccion) -> Direccion:
        self.session.add(direccion)
        self.session.flush()
        self.session.refresh(direccion)
        return direccion
    
    def delete(self, direccion: Direccion) -> None:
        self.session.delete(direccion)
        self.session.flush()
    
    def reset_principal_flag(self, usuario_id: int) -> None:
        statement = update(Direccion).where(
            Direccion.usuario_id == usuario_id,
            Direccion.es_principal == True
        ).values(es_principal=False)
        self.session.exec(statement)
        self.session.flush()