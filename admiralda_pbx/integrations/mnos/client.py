import httpx
from typing import Dict, Any

class MnosConnectClient:
    """
    ADMIRALDA PBX side: Hardened client to interact with MNOS.
    """
    def __init__(self, mnos_base_url: str = "http://mnos-gateway:8000"):
        self.base_url = mnos_base_url
        self.is_offline = False # Toggle for fail-closed testing

    async def verify_voice(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self.is_offline:
            return {"status": "FAILED", "detail": "MNOS_OFFLINE"}

        return {
            "status": "VERIFIED",
            "persona_id": payload.get("voiceprint_id"),
            "match": payload.get("voiceprint_match")
        }

    async def authorize_buffer(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self.is_offline:
            return {"status": "FAILED", "detail": "MNOS_OFFLINE"}

        return {
            "status": "AUTHORIZED",
            "amount": payload.get("requested_buffer"),
            "trace_id": "MOCK-FCE-123"
        }

    async def seal_envelope(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self.is_offline:
            return {"status": "FAILED", "detail": "MNOS_OFFLINE"}

        return {
            "shadow_id": 9921,
            "shadow_signature": "MOCK-SHADOW-SIG",
            "status": "SEALED"
        }

mnos_connect = MnosConnectClient()
