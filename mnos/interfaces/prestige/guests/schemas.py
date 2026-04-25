from typing import Optional
from datetime import date
from pydantic import BaseModel, EmailStr

class GuestBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    passport_number: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[date] = None

class GuestCreate(GuestBase):
    first_name: str
    last_name: str
    email: EmailStr
    trace_id: str

class GuestUpdate(GuestBase):
    pass

class Guest(GuestBase):
    id: int
    trace_id: Optional[str] = None

    class Config:
        from_attributes = True
