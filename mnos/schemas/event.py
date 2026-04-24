from pydantic import BaseModel
from typing import Any, Dict

class ProductionEventSchema(BaseModel):
    source: str
    tenant_id: str
    type: str
    data: Dict[str, Any]
