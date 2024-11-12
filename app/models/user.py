from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserBase(BaseModel):
    user_id: int = Field(..., example=1064260)  # Numeric User ID, fixed upon registration
    username: str = Field(..., example="johndoe", min_length=3, max_length=30)
    email: EmailStr = Field(..., example="johndoe@example.com")
    full_name: Optional[str] = Field(None, example="John Doe")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="strongpassword")

class UserResponse(UserBase):
    id: str = Field(..., example="605c72e57d3e2f001f3e5a2c")  # Example UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(None)

    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, example="johndoe_updated")
    email: Optional[EmailStr] = Field(None, example="johndoe_updated@example.com")
    full_name: Optional[str] = Field(None, example="John Doe Updated")
    password: Optional[str] = Field(None, min_length=8, example="newstrongpassword")