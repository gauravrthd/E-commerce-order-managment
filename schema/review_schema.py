from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class ReviewBase(BaseModel):
    user_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None


class ReviewCreate(ReviewBase):
    pass


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = None


class ReviewResponse(ReviewBase):
    id: int

    model_config = ConfigDict(from_attributes=True)