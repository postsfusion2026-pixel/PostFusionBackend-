from pydantic import BaseModel, EmailStr
from datetime import datetime

# what user sends to CREATE account
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

# what we send BACK to user (never send password!)
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True