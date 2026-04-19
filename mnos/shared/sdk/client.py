import os
import httpx
import uuid
import time
import hmac
import hashlib
import json
from typing import Dict, Any, Optional, Tuple
from .models import MnosEnvelope, ShadowEnvelope

class MnosClient:
    def __init__(self, base_url: str = "http://api-gateway:8000"):
        self.base_url = base_url
        self.secret = os.environ.get("MNOS_INTEGRATION_SECRET")
        if not self.secret:
            raise RuntimeError("MNOS_INTEGRATION_SECRET is missing")

    def _generate_signature(self, method: str, path: str, timestamp: str, request_id: str, body: bytes) -> str:
        body_hash = hashlib.sha256(body).hexdigest()
        canonical_string = f"{method.upper()}\n{path}\n{timestamp}\n{request_id}\n{body_hash}"
        return hmac.new(
            self.secret.encode(),
            canonical_string.encode(),
            hashlib.sha256
        ).hexdigest()

    def _get_headers(self, method: str, path: str, body_dict: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, str]:
        timestamp = str(int(time.time()))
        request_id = str(uuid.uuid4())
        body_bytes = json.dumps(body_dict, sort_keys=True).encode()

        signature = self._generate_signature(method, path, timestamp, request_id, body_bytes)

        headers = {
            "X-Signature": signature,
            "X-Timestamp": timestamp,
            "X-Request-Id": request_id,
            "Content-Type": "application/json"
        }

        headers["X-Idempotency-Key"] = idempotency_key or str(uuid.uuid4())

        return headers

    async def verify_aegis(self, token: str, action: str, resource: str) -> bool:
        path = "/api/core/aegis/verify"
        body = {"token": token, "action": action, "resource": resource}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{path}",
                json=body,
                headers=self._get_headers("POST", path, body),
                timeout=5.0
            )
            return response.status_code == 200

    async def decide_eleone(self, context: Dict[str, Any]) -> Tuple[str, str]:
        path = "/api/core/eleone/decide"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{path}",
                json=context,
                headers=self._get_headers("POST", path, context),
                timeout=5.0
            )
            data = response.json()
            return data.get("decision", "DENY"), data.get("policy_decision_id")

    async def publish_event(self, event_type: str, payload: Dict[str, Any]) -> str:
        path = "/api/core/events/publish"
        body = {"type": event_type, "payload": payload}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{path}",
                json=body,
                headers=self._get_headers("POST", path, body),
                timeout=5.0
            )
            data = response.json()
            return data.get("event_id")

    async def commit_shadow(self, transaction_id: str, event_id: str, data: Dict[str, Any]) -> str:
        path = "/api/core/shadow/commit"
        body = {"transaction_id": transaction_id, "event_id": event_id, "data": data}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{path}",
                json=body,
                headers=self._get_headers("POST", path, body),
                timeout=5.0
            )
            data = response.json()
            return data.get("shadow_id")

    async def calculate_fce(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        path = "/api/core/fce/calculate"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{path}",
                json=invoice_data,
                headers=self._get_headers("POST", path, invoice_data),
                timeout=5.0
            )
            return response.json()

    def create_response_envelope(self, module: str, transaction_id: str, status: str, data: Any = None, shadow_id: str = None, event_id: str = None, policy_decision_id: str = None) -> MnosEnvelope:
        return MnosEnvelope(
            module=module,
            transaction_id=transaction_id,
            status=status,
            data=data,
            shadow_id=shadow_id,
            event_id=event_id,
            policy_decision_id=policy_decision_id
        )
