from pydantic import BaseModel
from typing import Any, Dict, Optional

class MetricsData(BaseModel):
    success_count: int
    failure_count: int
    retry_count: int
    dead_letter_count: int
    last_processed_at: Optional[str]

class MetricsResponse(BaseModel):
    success: bool
    data: MetricsData

class HealthData(BaseModel):
    service: str
    status: str

class HealthResponse(BaseModel):
    success: bool
    data: HealthData
