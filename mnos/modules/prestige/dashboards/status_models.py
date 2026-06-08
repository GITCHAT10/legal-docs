from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from typing import List

class CommandStatus(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"
    BLACK = "BLACK"

class ArrivalRecord(BaseModel):
    booking_id: str
    guest_name: str
    arrival_time: datetime
    privacy_level: str
    status: CommandStatus = CommandStatus.GREEN
    issues: List[str] = []
    logistics_seal: bool = False
