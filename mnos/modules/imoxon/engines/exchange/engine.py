class ExchangeEngine:
    def __init__(self, guard, fce, shadow, events):
        self.guard = guard
        self.fce = fce
        self.shadow = shadow
        self.events = events

    def transfer_asset(self, actor_ctx: dict, transfer_data: dict):
        return self.guard.execute_sovereign_action(
            "imoxon.exchange.transfer",
            actor_ctx,
            self._internal_transfer,
            transfer_data
        )

    def _internal_transfer(self, data: dict):
        asset_id = data.get("asset_id")
        price = data.get("price", 0)
        pricing = self.fce.price_order(price)

        entry = {
            "seller": data.get("seller_id"),
            "buyer": self.guard.get_actor().get("identity_id"),
            "asset": asset_id,
            "pricing": pricing,
            "status": "TRANSFERRED"
        }
        self.events.publish("exchange.asset_transferred", entry)
        return entry
