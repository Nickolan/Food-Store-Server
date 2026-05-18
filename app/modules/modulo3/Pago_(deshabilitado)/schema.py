from datetime import datetime
from decimal import Decimal
from typing import Optional
from .model import PagoBase
from sqlmodel import Field, SQLModel
class PagoCreate(PagoBase):
    pedido_id:int

class PagoRead(PagoBase):
    id: int
    pedido_id:int
    created_at: datetime
    updated_at: datetime

class PagoUpdate(PagoBase):
    mp_payment_id: Optional[int] = None
    mp_status: Optional[str] = Field(default=None, max_length=30)
    mp_status_detail: Optional[str] = Field(default=None, max_length=100)
    external_reference: Optional[str] = Field(default=None, max_length=100)
    idempotency_key: Optional[str] = Field(default=None, max_length=100)
    transaction_amount: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2)
    payment_method_id: Optional[str] = Field(default=None, max_length=50)