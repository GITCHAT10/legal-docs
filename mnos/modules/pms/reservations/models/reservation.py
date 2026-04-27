from datetime import date, datetime, UTC
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import uuid

class Reservation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str
    idempotency_key: str
    guest_id: str
    room_type_id: str
    assigned_room_id: Optional[str] = None
    rate_plan_id: str
    check_in: date
    check_out: date
    status: str = "DRAFT" # DRAFT, PENDING, CONFIRMED, CHECKED_IN, CHECKED_OUT, CANCELLED
    total_amount: float
    currency: str = "USD"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self):
        data = self.model_dump()
        data["check_in"] = self.check_in.isoformat()
        data["check_out"] = self.check_out.isoformat()
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data

class AvailabilityCache(BaseModel):
    date: date
    room_type_id: str
    total_rooms: int
    allocated_rooms: int = 0
    blocked_until: Optional[datetime] = None
    version: int = 1

class ReservationStateLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reservation_id: str
    from_state: str
    to_state: str
    triggered_by: str
    execution_guard_result: Dict[str, Any]
    shadow_hash: str
    committed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
