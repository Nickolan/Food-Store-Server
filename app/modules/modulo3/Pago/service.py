import uuid
import mercadopago
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, status
from app.modules.modulo3.HistorialEstadoPedido.model import HistorialEstadoPedido
from app.modules.modulo3.Pago.model import Pago
from app.modules.modulo3.Pago.schema import PagoCreate, PagoRead, PagoUpdate
from app.modules.modulo3.Pago.unitOfWork import PagoUnitOfWork
from app.modules.modulo3.Pedido.service import PedidoService
from app.core.config import settings
from sqlmodel import select

class PagoService:
    def __init__(self, uow: PagoUnitOfWork):
        self.uow = uow
    
    def crear(self, data: PagoCreate) -> PagoRead:
        with self.uow as uow:
            pedido = uow.pedidos.get_by_id(data.pedido_id)
            if not pedido:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"El pedido con el id {data.pedido_id} no fue encontrado.")
            if pedido.estado_codigo != "PENDIENTE":
                raise HTTPException(
                    status_code=400,
                    detail=f"Solo se puede pagar un pedido en estado PENDIENTE. Estado actual: {pedido.estado_codigo}"
                )
            
            sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
            external_reference = pedido.id
            idempotency_key = str(uuid.uuid4())
            
            preference_data = {
                "items": [
                    {
                        "title": f"Pedido {pedido.id}",
                        "quantity": 1,
                        "currency_id": "ARS",
                        "unit_price": float(pedido.total)
                    }
                ],
                "back_urls": {
                    "success": f"{settings.FRONTEND_URL}/success?pedido={pedido.id}",
                    "failure": f"{settings.FRONTEND_URL}/failure?pedido={pedido.id}",
                    "pending": f"{settings.FRONTEND_URL}/pending?pedido={pedido.id}"
                },
                "external_reference": external_reference,
                "auto_return": "approved",
            }
            
            request_options = mercadopago.config.RequestOptions()
            request_options.custom_headers = {
                'x-idempotency-key': idempotency_key
            }
            
            preference_response = sdk.preference().create(preference_data, request_options)
            if preference_response.get("status") not in [200, 201]:
                error_msg = preference_response.get("response", {})
                raise HTTPException(status_code=400, detail=f"Error de Mercado Pago: {error_msg}")
                
            preference = preference_response["response"]
            init_point = preference.get("init_point")
            
            pago = Pago(**data.model_dump())
            pago.mp_status = "in_process"
            pago.external_reference = external_reference
            pago.idempotency_key = idempotency_key
            pago.transaction_amount = pedido.total
            pago.checkout_url = init_point
            
            nuevoPago = uow.pagos.add(pago)
            
            return PagoRead.model_validate(nuevoPago)
            
    def procesar_webhook(self, mp_payment_id: int):
        sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
        payment_response = sdk.payment().get(mp_payment_id)
        
        if payment_response.get("status") not in [200, 201]:
            return
            
        payment_info = payment_response.get("response", {})
        external_reference = payment_info.get("external_reference")
        mp_status = payment_info.get("status")
        mp_status_detail = payment_info.get("status_detail")
        
        with self.uow as uow:
            statement = select(Pago).where(Pago.external_reference == external_reference)
            pago = uow._session.exec(statement).first()
            
            if not pago:
                return
                
            pago.mp_status = mp_status
            pago.mp_status_detail = mp_status_detail
            pago.mp_payment_id = mp_payment_id
            
            if mp_status == "approved":
                pedido = uow.pedidos.get_by_id(pago.pedido_id)
                if pedido and pedido.estado_codigo != "CONFIRMADO":
                    pedido_service = PedidoService(uow=None)
                    pedido_service.avanzar_estado(
                        uow=uow, 
                        pedido=pedido, 
                        nuevo_codigo="CONFIRMADO", 
                        usuario_id=None, 
                        motivo="Pago acreditado por Mercado Pago"
                    )
            
            uow.pagos.add(pago)

    def obtener_todos(self, skip: int, limit: int) -> List[PagoRead]:
        with self.uow as uow:
            pagos = uow.pagos.get_all(skip, limit)
            return [PagoRead.model_validate(p) for p in pagos]
    
    def obtener_por_id(self, id: int) -> Optional[PagoRead]:
        with self.uow as uow:
            pago = uow.pagos.get_by_id(id)
            if not pago:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"El pago con el id {id} no fue encontrado.")
            return PagoRead.model_validate(pago)
    
    def actualizar(self, id: int, data: PagoUpdate) -> Optional[PagoRead]:
        with self.uow as uow:
            datos_nuevos = data.model_dump(exclude_unset=True)
            pago = uow.pagos.get_by_id(id)
            if not pago:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"El pago con el id {id} no fue encontrado.")
            for clave, valor in datos_nuevos.items():
                setattr(pago, clave, valor)
            pago.updated_at = datetime.now()
            uow.pagos.add(pago)
            return PagoRead.model_validate(pago)