from fastapi import HTTPException, status
from sqlmodel import Session
from app.modules.unidad_medida.models import UnidadMedida
from app.modules.unidad_medida.schemas import (
    UnidadMedidaCreate,
    UnidadMedidaUpdate,
    UnidadMedidaRead,
    UnidadMedidaPaginadoResponse
)
from app.modules.unidad_medida.unit_of_work import UnidadMedidaUnitOfWork

class UnidadMedidaService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _get_or_404(self, uow: UnidadMedidaUnitOfWork, unidad_id: int) -> UnidadMedida:
        unidad = uow.unidades_medida.get_by_id(unidad_id)
        if not unidad:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unidad de medida con id={unidad_id} no encontrada",
            )
        return unidad

    def crear(self, data: UnidadMedidaCreate) -> UnidadMedidaRead:
        with UnidadMedidaUnitOfWork(self._session) as uow:
            nuevo = UnidadMedida(**data.model_dump())
            uow.unidades_medida.add(nuevo)
            uow.commit()
            self._session.refresh(nuevo)
            return UnidadMedidaRead.model_validate(nuevo)

    def obtener_todas(self, offset: int = 0, limit: int = 20) -> UnidadMedidaPaginadoResponse:
        with UnidadMedidaUnitOfWork(self._session) as uow:
            unidades = uow.unidades_medida.get_all(offset=offset, limit=limit)
            total = uow.unidades_medida.count_all()
            items = [UnidadMedidaRead.model_validate(u) for u in unidades]
            return UnidadMedidaPaginadoResponse(total=total, items=items)

    def obtener_por_id(self, unidad_id: int) -> UnidadMedidaRead:
        with UnidadMedidaUnitOfWork(self._session) as uow:
            unidad = self._get_or_404(uow, unidad_id)
            return UnidadMedidaRead.model_validate(unidad)

    def actualizar(self, unidad_id: int, data: UnidadMedidaUpdate) -> UnidadMedidaRead:
        with UnidadMedidaUnitOfWork(self._session) as uow:
            unidad = self._get_or_404(uow, unidad_id)
            cambios = data.model_dump(exclude_unset=True)
            for key, value in cambios.items():
                setattr(unidad, key, value)
            uow.unidades_medida.add(unidad)
            uow.commit()
            self._session.refresh(unidad)
            return UnidadMedidaRead.model_validate(unidad)

    def eliminar(self, unidad_id: int) -> None:
        with UnidadMedidaUnitOfWork(self._session) as uow:
            unidad = self._get_or_404(uow, unidad_id)
            uow.unidades_medida.delete(unidad)
            uow.commit()
