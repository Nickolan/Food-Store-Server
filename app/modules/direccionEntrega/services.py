from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlmodel import select
from app.modules.direccionEntrega.models import DireccionEntrega
from app.modules.direccionEntrega.schemas import (
    DireccionCreate,
    DireccionUpdate,
    DireccionRead,
    DireccionPaginadoResponse,
)
from app.modules.direccionEntrega.unit_of_work import DireccionUoW

class DireccionService:
    """
    Servicio de Direcciones
    """

    def __init__(self, session) -> None:
        self._session = session

    # si no hay una dirección principal, la primera se vuelve principal automáticamente
    def _get_or_404(self, uow: DireccionUoW, direccion_id: int, usuario_id: int) -> DireccionEntrega:
        direccion = uow.direcciones.get_by_usuario(usuario_id, direccion_id)
        if not direccion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dirección con ID {direccion_id} no encontrada."
            )
        return direccion

    
    def _ensure_one_principal(self, uow: DireccionUoW, usuario_id: int, direccion_actual: Optional[DireccionEntrega] = None) -> None:
        """Asegura que el usuario tenga al menos una dirección principal"""
        direcciones = uow.direcciones.get_all_by_usuario(usuario_id)
        has_principal = any(d.es_principal for d in direcciones)
        
        if not has_principal and direcciones:
            primera = direcciones[0]
            if direccion_actual and primera.id == direccion_actual.id:
                primera.es_principal = True
            else:
                primera.es_principal = True
                uow.direcciones.add(primera)

    # Casos de uso
    def crear(self, usuario_id: int, data: DireccionCreate) -> DireccionRead:
        with DireccionUoW(self._session) as uow:
            if data.es_principal:
                uow.direcciones.reset_principal_flag(usuario_id)
            
            direccion = DireccionEntrega(
                usuario_id=usuario_id,
                **data.model_dump()
            )
            
            existing_count = uow.direcciones.count_by_usuario(usuario_id)
            if existing_count == 0:
                direccion.es_principal = True
            
            uow.direcciones.add(direccion)
            result = DireccionRead.model_validate(direccion)
        return result

    def listar_por_usuario(self, usuario_id: int) -> List[DireccionRead]:
        with DireccionUoW(self._session) as uow:
            direcciones = uow.direcciones.get_all_by_usuario(usuario_id)
            result = [DireccionRead.model_validate(d) for d in direcciones]
        return result

    def obtener_por_id(self, usuario_id: int, direccion_id: int) -> DireccionRead:
        with DireccionUoW(self._session) as uow:
            direccion = self._get_or_404(uow, direccion_id, usuario_id)
            result = DireccionRead.model_validate(direccion)
        return result

    def actualizar(self, usuario_id: int, direccion_id: int, data: DireccionUpdate) -> DireccionRead:
        with DireccionUoW(self._session) as uow:
            direccion = self._get_or_404(uow, direccion_id, usuario_id)
            
            update_data = data.model_dump(exclude_unset=True)
            
            if update_data.get("es_principal") and not direccion.es_principal:
                uow.direcciones.reset_principal_flag(usuario_id)
            
            for key, value in update_data.items():
                setattr(direccion, key, value)
            
            direccion.updated_at = datetime.now(timezone.utc)
            uow.direcciones.add(direccion)
            
            self._ensure_one_principal(uow, usuario_id, direccion)
            
            result = DireccionRead.model_validate(direccion)
        return result

    def eliminar(self, usuario_id: int, direccion_id: int) -> None:
        with DireccionUoW(self._session) as uow:
            direccion = self._get_or_404(uow, direccion_id, usuario_id)
            
            direcciones = uow.direcciones.get_all_by_usuario(usuario_id)
            if len(direcciones) == 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se puede eliminar la única dirección del usuario."
                )
            
            was_principal = direccion.es_principal
            
            direccion.deleted_at = datetime.now(timezone.utc)
            uow.direcciones.add(direccion)
            
            if was_principal:
                self._ensure_one_principal(uow, usuario_id)

    def marcar_como_principal(self, usuario_id: int, direccion_id: int) -> DireccionRead:
        with DireccionUoW(self._session) as uow:
            direccion = self._get_or_404(uow, direccion_id, usuario_id)

            if not direccion.es_principal:
                uow.direcciones.reset_principal_flag(usuario_id)
                direccion.es_principal = True
                direccion.updated_at = datetime.now(timezone.utc)
                uow.direcciones.add(direccion)

            result = DireccionRead.model_validate(direccion)
        return result
    
    def obtener_por_id_admin(self, direccion_id: int) -> DireccionRead:
        with DireccionUoW(self._session) as uow:
            direccion = uow.direcciones.get_by_id_admin(direccion_id)
            if not direccion:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Dirección con ID {direccion_id} no encontrada."
                )
            result = DireccionRead.model_validate(direccion)
        return result