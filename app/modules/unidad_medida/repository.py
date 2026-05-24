from sqlmodel import Session, select
from app.core.repository import BaseRepository
from app.modules.unidad_medida.models import UnidadMedida

class UnidadMedidaRepository(BaseRepository[UnidadMedida]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, UnidadMedida)

    def count_all(self) -> int:
        return len(self.session.exec(select(UnidadMedida)).all())
