from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel
class HistorialEstadoPedidoRead(SQLModel):
    pedido_id: int
    estado_desde: Optional[str]
    estado_hacia: str
    usuario_id: Optional[int]
    motivo: Optional[str]
    created_at: datetime