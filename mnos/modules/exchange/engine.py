import uuid
from datetime import datetime, UTC

class ExchangeEngine:
    def __init__(self, core):
        self.core = core

    def transfer_asset(self, actor_ctx: dict, transfer_data: dict):
        return self.core.execute_commerce_action(
            "exchange.asset.transfer",
            actor_ctx,
            self._internal_transfer,
            transfer_data
        )

    def _internal_transfer(self, data):
        transfer = {
            "transfer_id": f"EX-{uuid.uuid4().hex[:6].upper()}",
            "asset_id": data.get("asset_id"),
            "seller_id": data.get("seller_id"),
            "buyer_id": self.core.guard.get_actor().get("identity_id"),
            "price": data.get("price"),
            "status": "FINALIZED"
        }
        self.core.events.publish("exchange.transfer_completed", transfer)
        return transfer
