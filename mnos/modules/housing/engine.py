import uuid

class HousingEngine:
    def __init__(self, core):
        self.core = core
        self.leases = {}

    def create_lease(self, actor_ctx: dict, lease_data: dict):
        return self.core.execute_commerce_action(
            "housing.lease.create",
            actor_ctx,
            self._internal_lease,
            lease_data
        )

    def _internal_lease(self, data):
        lease = {
            "lease_id": f"LSE-{uuid.uuid4().hex[:6].upper()}",
            "property": data.get("property"),
            "tenant_id": self.core.guard.get_actor().get("identity_id"),
            "rent": data.get("rent"),
            "status": "ACTIVE"
        }
        self.core.events.publish("housing.lease_signed", lease)
        return lease
