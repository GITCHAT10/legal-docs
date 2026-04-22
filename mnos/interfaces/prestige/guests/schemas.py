from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class GuestBase(BaseModel):
    full_name: str
    email: EmailStr

class GuestCreate(GuestBase):
    pass

class Guest(GuestBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
