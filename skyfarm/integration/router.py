from fastapi import APIRouter
from skyfarm.integration.service import create_integration_event
import requests
from pydantic import BaseModel
from typing import Any, Dict

router = APIRouter()

MNOS_URL = "http://localhost:8000"

class IntegrationSend(BaseModel):
    event_id: str
    tenant_id: str
    event_type: str
    category: str # e.g., "production", "logistics", "finance", "aeigis", "shadow"
    data: Dict[str, Any]

@router.post("/integration/send")
def send_to_mnos(payload: IntegrationSend):
    event = create_integration_event(payload.event_id, payload.tenant_id, payload.event_type, payload.data)

    # Map category to MNOS endpoint
    if payload.category.lower() in ["aeigis", "aegis"]:
        endpoint = f"{MNOS_URL}/integration/v1/events/aegis"
    elif payload.category.lower() == "shadow":
         endpoint = f"{MNOS_URL}/integration/v1/events/shadow"
    else:
        endpoint = f"{MNOS_URL}/integration/v1/events/{payload.category}"

    try:
        resp = requests.post(endpoint, json=event.dict())
        return resp.json()
    except Exception as e:
        return {"error": str(e)}
