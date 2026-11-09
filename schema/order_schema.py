from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class OrderBase(BaseModel):
    user_id: int = Field(gt=0)
    total_amount: float = Field(ge=0)
    shipping_address: str
    order_status: str = "pending"


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    shipping_address: Optional[str] = None
    order_status: Optional[str] = None


class OrderResponse(OrderBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)