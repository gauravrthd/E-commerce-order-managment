from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class CancellationBase(BaseModel):
    order_id: int = Field(gt=0)
    reason: str = Field(min_length=5)
    cancellation_status: str = "pending"


class CancellationCreate(CancellationBase):
    pass


class CancellationUpdate(BaseModel):
    cancellation_status: Optional[str] = None


class CancellationResponse(CancellationBase):
    id: int

    model_config = ConfigDict(from_attributes=True)