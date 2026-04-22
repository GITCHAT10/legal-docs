import httpx
import logging
from typing import Dict, Any, Optional
from mnos.core.security.config import settings

class NexusClient:
    """
    Standalone NEXUS SKY-i API Client.
    Connects UT to our Sovereign stack via signed API only.
    """
    def __init__(self, base_url: str = "http://nexus-sky-i:8000/api/v1"):
        self.base_url = base_url
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    def _get_headers(self, patente: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "X-UT-Internal-Secret": settings.SECRET_KEY,
            "Content-Type": "application/json"
        }
        if patente:
            headers["X-NexGen-Patente"] = patente
        return headers

    async def verify_session(self, token: str, patente: str) -> bool:
        """AEGIS: verify-session / trusted operator validation."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # Mock calling NEXUS AEGIS bridge
                res = await client.get(
                    f"{self.base_url}/auth/verify",
                    headers={"Authorization": f"Bearer {token}", "X-NexGen-Patente": patente}
                )
                return res.status_code == 200
            except Exception as e:
                logging.error(f"NEXUS AEGIS error: {e}")
                return False

    async def preauthorize_payment(self, amount: float, trace_id: str) -> bool:
        """FCE: preauthorize payment via NEXUS FCE module."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                res = await client.post(
                    f"{self.base_url}/finance/preauth",
                    json={"amount": amount, "trace_id": trace_id},
                    headers=self._get_headers()
                )
                return res.status_code == 200
            except Exception as e:
                logging.error(f"NEXUS FCE error: {e}")
                return False

    async def commit_evidence(self, trace_id: str, payload: Dict[str, Any]) -> bool:
        """SHADOW: commit evidence path."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                res = await client.post(
                    f"{self.base_url}/shadow/commit",
                    json={"trace_id": trace_id, "evidence": payload},
                    headers=self._get_headers()
                )
                return res.status_code == 200
            except Exception as e:
                logging.error(f"NEXUS SHADOW error: {e}")
                return False

    async def publish_event(self, event_type: str, data: Dict[str, Any]):
        """EVENTS: publish callbacks."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                await client.post(
                    f"{self.base_url}/events/publish",
                    json={"type": event_type, "data": data},
                    headers=self._get_headers()
                )
            except Exception as e:
                logging.error(f"NEXUS EVENTS error: {e}")

nexus_client = NexusClient()
