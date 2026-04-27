from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class EmailEvent(BaseModel):
    email: str
    event: str # opened, clicked, replied
    campaign: str
    timestamp: datetime

class ExmailStats(BaseModel):
    emails_sent: int
    opens: int
    clicks: int
    replies: int
    conversion_rate: float

class Campaign(BaseModel):
    name: str
    region: str
    priority: str
    sent: int
    opens: int
    clicks: int
    replies: int
    status: str
