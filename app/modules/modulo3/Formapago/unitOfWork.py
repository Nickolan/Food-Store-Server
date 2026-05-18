from app.core.unit_of_work import UnitOfWork
from app.modules.modulo3.Formapago.repository import FormaPagoRepository


class FormaPagoUnitOfWork(UnitOfWork):
    def __enter__(self):
        super().__enter__()
        self.formaspago=FormaPagoRepository(self._session)
        return self