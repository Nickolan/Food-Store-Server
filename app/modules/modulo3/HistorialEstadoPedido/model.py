from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime
class HistorialEstadoPedido(SQLModel,table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pedido_id: int = Field(
        foreign_key="pedido.id", 
        nullable=False, 
        ondelete="CASCADE"
    )
    estado_desde: Optional[str] = Field(
        default=None, 
        foreign_key="estadopedido.codigo", 
        max_length=20
    )
    estado_hacia: str = Field(
        foreign_key="estadopedido.codigo", 
        max_length=20, 
        nullable=False
    )
    usuario_id: Optional[int] = Field(
        default=None, 
        foreign_key="usuario.id"
    )
    
    motivo: Optional[str] = Field(default=None) 
    
    created_at: datetime = Field(
        default_factory=datetime.now, 
        nullable=False
    )