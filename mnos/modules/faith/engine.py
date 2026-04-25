import uuid
from datetime import datetime, UTC

class FaithEngine:
    def __init__(self, core):
        self.core = core
        self.contributions = {}

    def donate(self, actor_ctx: dict, donation_data: dict):
        return self.core.execute_commerce_action(
            "faith.donation.process",
            actor_ctx,
            self._internal_donate,
            donation_data
        )

    def _internal_donate(self, data):
        # Faith contributions are tax-exempt in N-DEOS logic
        amount = data.get("amount")
        contribution = {
            "ref_id": f"ZKT-{uuid.uuid4().hex[:6].upper()}",
            "donor_id": self.core.guard.get_actor().get("identity_id"),
            "amount": float(amount),
            "type": data.get("type"), # ZAKAT, SADAQAH
            "tax_exempt": True,
            "timestamp": datetime.now(UTC).isoformat()
        }
        self.core.events.publish("faith.donation_received", contribution)
        return contribution
