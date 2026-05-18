from typing import List
from fastapi import HTTPException, status
from app.modules.direccion.models import Direccion
from app.modules.direccion.schemas import DireccionCreate, DireccionUpdate
from app.modules.direccion.unit_of_work import DireccionUoW

class DireccionService:
    def __init__(self, uow: DireccionUoW):
        self.uow = uow
    
    def create_direccion(self, usuario_id: int, direccion_data: DireccionCreate) -> Direccion:
        """Crear una nueva dirección para el usuario"""
        with self.uow:
            if direccion_data.es_principal:
                self.uow.direcciones.reset_principal_flag(usuario_id)
            
            new_direccion = Direccion(
                usuario_id=usuario_id,
                **direccion_data.model_dump()
            )
            
            existing_direcciones = self.uow.direcciones.get_all_by_usuario(usuario_id)
            if not existing_direcciones:
                new_direccion.es_principal = True
            
            created = self.uow.direcciones.create(new_direccion)
            return created
    
    def get_direcciones_by_usuario(self, usuario_id: int) -> List[Direccion]:
        with self.uow:
            return self.uow.direcciones.get_all_by_usuario(usuario_id)
    
    def get_direccion_by_id(self, direccion_id: int, usuario_id: int) -> Direccion:
        with self.uow:
            direccion = self.uow.direcciones.get_by_id(direccion_id, usuario_id)
            if not direccion:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dirección no encontrada"
                )
            return direccion
    
    def update_direccion(
        self, 
        direccion_id: int, 
        usuario_id: int, 
        update_data: DireccionUpdate
    ) -> Direccion:
        with self.uow:
            direccion = self.uow.direcciones.get_by_id(direccion_id, usuario_id)
            if not direccion:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dirección no encontrada"
                )
            
            if update_data.es_principal and not direccion.es_principal:
                self.uow.direcciones.reset_principal_flag(usuario_id)
            
            update_dict = update_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                setattr(direccion, key, value)
            
            direcciones_count = len(self.uow.direcciones.get_all_by_usuario(usuario_id))
            if direcciones_count == 1 and not direccion.es_principal:
                direccion.es_principal = True
            
            updated = self.uow.direcciones.update(direccion)
            self.uow.commit()
            return updated
    
    def delete_direccion(self, direccion_id: int, usuario_id: int) -> None:
        with self.uow:
            direccion = self.uow.direcciones.get_by_id(direccion_id, usuario_id)
            if not direccion:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dirección no encontrada"
                )
            
            direcciones = self.uow.direcciones.get_all_by_usuario(usuario_id)
            if len(direcciones) == 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se puede eliminar la única dirección del usuario"
                )
            
            was_principal = direccion.es_principal
            
            self.uow.direcciones.delete(direccion)
            
            if was_principal:
                remaining_direcciones = self.uow.direcciones.get_all_by_usuario(usuario_id)
                if remaining_direcciones:
                    new_principal = remaining_direcciones[0]
                    new_principal.es_principal = True
                    self.uow.direcciones.update(new_principal)
            
            self.uow.commit()