from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class CartBase(BaseModel):
    user_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class CartCreate(CartBase):
    pass


class CartUpdate(BaseModel):
    quantity: Optional[int] = Field(default=None, gt=0)


class CartResponse(CartBase):
    id: int

    model_config = ConfigDict(from_attributes=True)