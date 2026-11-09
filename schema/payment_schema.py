from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class PaymentBase(BaseModel):
    order_id: int = Field(gt=0)
    amount: float = Field(gt=0)
    payment_method: str
    payment_status: str = "pending"


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    payment_status: Optional[str] = None


class PaymentResponse(PaymentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)