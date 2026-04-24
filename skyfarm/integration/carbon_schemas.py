from pydantic import BaseModel
from typing import Optional

class CarbonRetireEvent(BaseModel):
    guest_name: str
    amount_kg: float = 14.5
    correlation_id: Optional[str] = None
    signature: Optional[str] = None
