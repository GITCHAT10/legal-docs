import os
import httpx
import uuid
from typing import Dict, Any, Optional
from .models import MnosEnvelope, ShadowEnvelope

class MnosClient:
    def __init__(self, base_url: str = "http://api-gateway:8000"):
        self.base_url = base_url
        self.secret = os.environ.get("MNOS_INTEGRATION_SECRET")
        if not self.secret:
            raise RuntimeError("MNOS_INTEGRATION_SECRET is missing")

    async def verify_aegis(self, token: str, action: str, resource: str) -> bool:
        # Implementation for AEGIS verification
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/core/aegis/verify",
                json={"token": token, "action": action, "resource": resource},
                timeout=5.0
            )
            return response.status_code == 200

    async def decide_eleone(self, context: Dict[str, Any]) -> str:
        # Implementation for ELEONE decision
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/core/eleone/decide",
                json=context,
                timeout=5.0
            )
            data = response.json()
            return data.get("decision", "DENY")

    async def publish_event(self, event_type: str, payload: Dict[str, Any]) -> str:
        # Implementation for EVENTS publishing
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/core/events/publish",
                json={"type": event_type, "payload": payload},
                timeout=5.0
            )
            data = response.json()
            return data.get("event_id")

    async def commit_shadow(self, transaction_id: str, event_id: str, data: Dict[str, Any]) -> str:
        # Implementation for SHADOW commit
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/core/shadow/commit",
                json={"transaction_id": transaction_id, "event_id": event_id, "data": data},
                timeout=5.0
            )
            data = response.json()
            return data.get("shadow_id")

    async def calculate_fce(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation for FCE calculation
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/core/fce/calculate",
                json=invoice_data,
                timeout=5.0
            )
            return response.json()

    def create_response_envelope(self, module: str, transaction_id: str, status: str, data: Any = None, shadow_id: str = None, event_id: str = None) -> MnosEnvelope:
        return MnosEnvelope(
            module=module,
            transaction_id=transaction_id,
            status=status,
            data=data,
            shadow_id=shadow_id,
            event_id=event_id
        )
