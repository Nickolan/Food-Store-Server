from decimal import Decimal
from typing import Optional
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel

from app.modules.modulo3.Pedido.model import Pedido


class PagoBase(SQLModel):
    mp_payment_id: Optional[int] = Field(default=None, sa_column_kwargs={"unique": True})
    mp_status: str = Field(max_length=30, nullable=False)  
    mp_status_detail: Optional[str] = Field(default=None, max_length=100)  
    external_reference: str = Field(max_length=100, unique=True, nullable=False)
    idempotency_key: str = Field(max_length=100, unique=True, nullable=False)
    transaction_amount: Decimal = Field(max_digits=10, decimal_places=2, nullable=False)
    payment_method_id: str = Field(max_length=50, nullable=False)
class Pago(PagoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    pedido_id: int = Field(foreign_key="pedido.id", nullable=False)
    pedido: Optional["Pedido"] = Relationship(back_populates="pagos")
    
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False)