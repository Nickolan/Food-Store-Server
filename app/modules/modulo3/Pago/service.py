from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, status
from app.modules.modulo3.HistorialEstadoPedido.model import HistorialEstadoPedido
from app.modules.modulo3.Pago.model import Pago
from app.modules.modulo3.Pago.schema import PagoCreate, PagoRead, PagoUpdate
from app.modules.modulo3.Pago.unitOfWork import PagoUnitOfWork
from app.modules.modulo3.Pedido.service import PedidoService

class PagoService:
    def __init__(self,uow:PagoUnitOfWork):
        self.uow=uow
    
    def crear(self,data:PagoCreate)->Pago:
        with self.uow as uow:
            pedido=uow.pedidos.obtener_por_id(data.pedido_id)
            if not pedido:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"El pedido con el id {data.pedido_id} no fue encontrado.")
            if pedido.estado_codigo != "PENDIENTE":
                raise HTTPException(
                    status_code=400,
                    detail=f"Solo se puede pagar un pedido en estado PENDIENTE. Estado actual: {pedido.estado_codigo}"
                )
            pago=Pago(**data.model_dump())
            pedido_service=PedidoService(uow=None)
            pedido_service.avanzar_estado(uow=uow, pedido=pedido, nuevo_estado="CONFIRMADO", usuario_id=None, motivo="Pago aprobado")
            uow.pedidos.crear(pedido)
            nuevoPago=uow.pagos.crear(pago)
            
            return PagoRead.model_validate(nuevoPago)
    
    def obtener_todos(self,skip:int,limit:int)->List[Pago]:
        with self.uow as uow:
            pagos=uow.pagos.obtener_todos(skip,limit)
            return [PagoRead.model_validate(p) for p in pagos]
    
    def obtener_por_id(self,id:int)->Optional[Pago]:
        with self.uow as uow:
            pago=uow.pagos.obtener_por_id(id)
            if not pago:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"El pago con el id {id} no fue encontrado.")
            return PagoRead.model_validate(pago)
    
    def actualizar(self,id:int,data:PagoUpdate)->Optional[Pago]:
        with self.uow as uow:
            datos_nuevos=data.model_dump(exclude_unset=True)
            pago=uow.pagos.obtener_por_id(id)
            if not pago:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"El pago con el id {id} no fue encontrado.")
            for clave, valor in datos_nuevos.items():
                setattr(pago, clave, valor)
            pago.updated_at = datetime.now()
            uow.pagos.crear(pago)
            return PagoRead.model_validate(pago)
    
  