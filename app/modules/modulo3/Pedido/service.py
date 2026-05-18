from datetime import datetime
from typing import List, Optional, Union
from fastapi import HTTPException, status
from sqlmodel import select
from app.modules.modulo3 import HistorialEstadoPedido, Pedido
from app.modules.modulo3.HistorialEstadoPedido.schema import HistorialEstadoPedidoRead
from app.modules.modulo3.Pedido.model import DetallePedido
from app.modules.modulo3.Pedido.schema import PedidoCreate, PedidoRead, PedidoUpdate
from app.modules.modulo3.Pedido.unitOfWork import PedidoUnitOfWork


class PedidoService:
    def __init__(self,uow:PedidoUnitOfWork):
        self.uow=uow
    def avanzar_estado(self,uow,pedido:Pedido,nuevo_codigo:str,usuario_id: Optional[int] = None, motivo: str = "Cambio de estado", es_creacion:bool=False, usuario_rol: Optional[str] = None):
        if es_creacion:
          historial = HistorialEstadoPedido(
            pedido_id=pedido.id,
            estado_desde=None,  
            estado_hacia=nuevo_codigo,
            usuario_id=usuario_id,
            motivo=motivo
          )
          uow.historiales.add(historial)
          return
        if pedido.estado_codigo == nuevo_codigo:
            return
        estado_actual = uow.estados.obtener_por_codigo(pedido.estado_codigo)
        nuevo_estado = uow.estados.obtener_por_codigo(nuevo_codigo)
        if not nuevo_estado:
            raise HTTPException(status_code=404, detail=f"El estado {nuevo_codigo} no existe.")
        if estado_actual and estado_actual.es_terminal:
            raise HTTPException(status_code=400, detail="No se puede cambiar el estado de un pedido terminal.")
       
        TRANSICIONES_PERMITIDAS = {
           "PENDIENTE": ["CONFIRMADO", "CANCELADO"],
           "CONFIRMADO": ["EN_PREP", "CANCELADO"],
           "EN_PREP": ["EN_CAMINO", "CANCELADO"],
           "EN_CAMINO": ["ENTREGADO"]
        }
        origen= pedido.estado_codigo.upper() if pedido.estado_codigo else None
        destino= nuevo_codigo.upper()
        if origen in TRANSICIONES_PERMITIDAS:
            if destino not in TRANSICIONES_PERMITIDAS[origen]:
                raise HTTPException(status_code=400, detail=f"No se puede cambiar el estado de {origen} a {destino}. Transiciones permitidas: {TRANSICIONES_PERMITIDAS[origen]}")
        else:
            raise HTTPException(status_code=400, detail=f"Estado de origen desconocido: {origen}. Estados conocidos: {list(TRANSICIONES_PERMITIDAS.keys())}")
        if origen == "EN_PREP" and destino == "CANCELADO":
         if usuario_rol not in ["ADMIN", "PEDIDOS"]:
            raise HTTPException(
                status_code=403, 
                detail="Permisos insuficientes: Solo ADMIN o PEDIDOS pueden cancelar un pedido en preparación."
            )
        estado_anterior = pedido.estado_codigo
        pedido.estado_codigo = nuevo_codigo
        pedido.updated_at = datetime.now()
        historial = HistorialEstadoPedido(
            pedido_id=pedido.id,
            estado_desde=estado_anterior,
            estado_hacia=nuevo_codigo,
            usuario_id=usuario_id,
            motivo=motivo
        )
        uow.historiales.add(historial)
    def validar_entidades(self,uow,data:Union[PedidoCreate,PedidoUpdate]):
            # Validar usuario
            usuario_id = getattr(data, "usuario_id", None) 
            if usuario_id:
             if not uow.usuarios.get_by_id(usuario_id):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"El usuario con el id {usuario_id} no fue encontrado.")
            
            # Validar dirección de entrega 
            direccion_id = getattr(data, "direccion_id", None)
            if direccion_id:
             if not uow.direcciones.get_by_id(direccion_id):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"La dirección con el id {direccion_id} no fue encontrada.")
            
            # Validar estado del pedido
            estado_codigo = getattr(data, "estado_codigo", None)
            if estado_codigo:
             if not uow.estados.get_by_codigo(estado_codigo):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"El estado con el código {estado_codigo} no fue encontrado.")
            
            # Validar forma de pago
            forma_pago_codigo = getattr(data, "forma_pago_codigo", None)
            if forma_pago_codigo:
             if not uow.formapago.get_by_codigo(forma_pago_codigo):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"La forma de pago con el código {forma_pago_codigo} no fue encontrada.")
            
    def crear(self,data:PedidoCreate)->PedidoRead:
        with self.uow as uow:
            self.validar_entidades(uow,data)
            datos_pedido = data.model_dump(exclude={"items"})
            pedido = Pedido(**datos_pedido)
            acumulado_subtotal=0.0
            detalles_finales=[]

            if data.items:
                for item in data.items:
                    producto = uow.productos.get_by_id(item.producto_id)
                    if not producto:
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"El producto con el id {item.producto_id} no fue encontrado.")
                    subtotal = producto.precio * item.cantidad
                    acumulado_subtotal += subtotal
                    detalle=DetallePedido(
                        producto_id=item.producto_id,
                        cantidad=item.cantidad,
                        subtotal_snap=subtotal,
                        nombre_snapshot=producto.nombre,
                        precio_snapshot=producto.precio,
                        personalizacion=item.personalizacion 
                    )
                    detalles_finales.append(detalle)
            pedido.subtotal=acumulado_subtotal
            pedido.total=pedido.subtotal - pedido.descuento + pedido.costo_envio
            pedido.detalle=detalles_finales
            nuevo_pedido=uow.pedidos.add(pedido)
            self.avanzar_estado(uow=uow,pedido=nuevo_pedido,nuevo_codigo=nuevo_pedido.estado_codigo, usuario_id=nuevo_pedido.usuario_id, motivo="Creación del pedido", es_creacion=True)
            return PedidoRead.model_validate(nuevo_pedido)
    
    def obtener_pedidos_por_usuario(self, usuario_id:int, skip:int, limit:int)->List[PedidoRead]:
        with self.uow as uow:
            pedidos=uow.pedidos.obtener_por_usuario(usuario_id, skip, limit)
            return [PedidoRead.model_validate(p) for p in pedidos]
    def obtener_todos(self,skip:int,limit:int)->List[PedidoRead]:
        with self.uow as uow:
            pedidos=uow.pedidos.get_all(skip,limit)
            return [PedidoRead.model_validate(p) for p in pedidos]
    
    def obtener_por_id(self,id:int)->Optional[PedidoRead]:
        with self.uow as uow:
            pedido=uow.pedidos.get_by_id(id)
            if not pedido:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"El pedido con el id {id} no fue encontrado.")
            return PedidoRead.model_validate(pedido)
    
    def actualizar(self,id:int,data:PedidoUpdate, usuario_rol:Optional[str])->Optional[PedidoRead]:
       with self.uow as uow:
           self.validar_entidades(uow,data)
           pedido=uow.pedidos.get_by_id(id)
           if not pedido:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"El pedido con el id {id} no fue encontrado.")
           datos_nuevos=data.model_dump(exclude_unset=True)
           if "estado_codigo" in datos_nuevos:
                motivo_cambio = "Cambio de estado mediante la actualización del pedido"
                if datos_nuevos["estado_codigo"].upper() =="CANCELADO":
                    if not data.notas or not data.notas.strip(): # este strip es para validar que no lo mandaron vacio
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="RN-05: El motivo es estrictamente obligatorio si el estado es CANCELADO. Por favor, especifíquelo en el campo 'notas'."
                        )
                    motivo_cambio = data.notas.strip()
                self.avanzar_estado(uow=uow,pedido=pedido,nuevo_codigo=datos_nuevos["estado_codigo"], usuario_id=pedido.usuario_id, motivo=motivo_cambio, usuario_rol=usuario_rol)
                datos_nuevos.pop("estado_codigo")
           for clave, valor in datos_nuevos.items():
                setattr(pedido, clave, valor)
           pedido.updated_at = datetime.now()
           uow.pedidos.add(pedido)
           return PedidoRead.model_validate(pedido)
    def obtener_historial(self,id:int)->List[HistorialEstadoPedidoRead]:
        with self.uow as uow:
            pedido=uow.pedidos.get_by_id(id)
            if not pedido:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"El pedido con el id {id} no fue encontrado.")
            historiales=uow.historiales.obtener_por_pedido(id)
            return [HistorialEstadoPedidoRead.model_validate(h) for h in historiales]
    def borrado_logico(self,id:int)->Optional[PedidoRead]:
        with self.uow as uow:
            pedido=uow.pedidos.borrado_logico(id)
            if not pedido:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"El pedido con el id {id} no fue encontrado.")
            return PedidoRead.model_validate(pedido)