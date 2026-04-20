import hmac
import hashlib
import time
import uuid
import json
import os
from typing import Any, Dict, Optional
from datetime import datetime, timezone

class MnosClient:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.secret = os.environ.get("MNOS_INTEGRATION_SECRET", "dev_secret")

    def _json_serial(self, obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    def _generate_signature(self, method: str, path: str, timestamp: str, request_id: str, body: str) -> str:
        body_hash = hashlib.sha256(body.encode()).hexdigest()
        canonical_string = f"{method.upper()}\n{path}\n{timestamp}\n{request_id}\n{body_hash}"
        return hmac.new(
            self.secret.encode(),
            canonical_string.encode(),
            hashlib.sha256
        ).hexdigest()

    def _get_headers(self, method: str, path: str, body: Dict[str, Any]) -> Dict[str, str]:
        timestamp = str(int(time.time()))
        request_id = str(uuid.uuid4())
        body_json = json.dumps(body, default=self._json_serial)
        signature = self._generate_signature(method, path, timestamp, request_id, body_json)

        return {
            "X-Signature": signature,
            "X-Timestamp": timestamp,
            "X-Request-Id": request_id,
            "X-Idempotency-Key": str(uuid.uuid4()),
            "X-Correlation-Id": str(uuid.uuid4()),
            "Content-Type": "application/json"
        }

    async def emit_event(self, event_type: str, payload: Dict[str, Any]):
        path = "/events"
        body = {
            "event_type": event_type,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        headers = self._get_headers("POST", path, body)
        # In a real implementation, we would use httpx to send the request
        print(f"[MnosClient] Emitting event {event_type} with payload: {payload}")
        return {"status": "success", "event_type": event_type}

    async def push_to_shadow(self, payload: Dict[str, Any], trace_id: str):
        path = "/shadow"
        body = {
            "payload": payload,
            "trace_id": trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        headers = self._get_headers("POST", path, body)
        # In a real implementation, we would use httpx to send the request
        print(f"[MnosClient] Pushing to SHADOW with trace_id {trace_id}")
        return {"status": "success", "trace_id": trace_id}
