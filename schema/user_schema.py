from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional


class UserBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    mobile: str = Field(min_length=10, max_length=15)
    role: str = Field(default="customer")


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2)
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None


class UserResponse(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)