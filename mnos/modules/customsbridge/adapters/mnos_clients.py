import httpx
from app.config import settings

class BaseMnosClient:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = httpx.AsyncClient(timeout=10.0)
        return cls._client

    def __init__(self, base_url: str):
        self.base_url = base_url

    async def post(self, endpoint: str, payload: dict):
        client = self.get_client()
        response = await client.post(f"{self.base_url}{endpoint}", json=payload)
        return response.json()

    async def get(self, endpoint: str):
        client = self.get_client()
        response = await client.get(f"{self.base_url}{endpoint}")
        return response.json()

class AquaClient(BaseMnosClient):
    async def verify_batches(self, batch_ids: list):
        return await self.post("/v1/aqua/batches/verify", {"batch_ids": batch_ids})

class OdysseyClient(BaseMnosClient):
    async def validate_yield(self, batch_ids: list, declared_weight: float):
        return await self.post("/v1/odyssey/yield/validate", {"batch_ids": batch_ids, "declared_weight": declared_weight})

class SkyGodownClient(BaseMnosClient):
    async def check_export_readiness(self, batch_ids: list):
        return await self.post("/v1/skygodown/export/readiness", {"batch_ids": batch_ids})

class FceClient(BaseMnosClient):
    async def check_settlement(self, batch_ids: list):
        return await self.post("/v1/fce/settlement/check", {"batch_ids": batch_ids})

class AegisClient(BaseMnosClient):
    async def trigger_port_lock(self, asset_id: str, reason: str, request_id: str, simulate: bool = True):
        endpoint = "/v1/aegis/port-lock/simulate" if simulate else "/v1/aegis/port-lock/engage"
        payload = {
            "asset_type": "CONTAINER",
            "asset_id": asset_id,
            "reason": reason,
            "source_module": "MNOS.CUSTOMSBRIDGE",
            "request_id": request_id
        }
        return await self.post(endpoint, payload)

class ShadowClient(BaseMnosClient):
    async def write_record(self, data: dict):
        return await self.post("/v1/shadow/records/write", data)

class EventsClient(BaseMnosClient):
    async def publish_event(self, event_type: str, payload: dict):
        return await self.post("/v1/events/publish", {"event_type": event_type, "payload": payload})

class EleoneClient(BaseMnosClient):
    async def get_risk_score(self, data: dict):
        return await self.post("/v1/eleone/risk-score", data)
