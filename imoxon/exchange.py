class ExchangeEngine:
    def __init__(self, shadow, event_bus):
        self.shadow = shadow
        self.event_bus = event_bus
        self.escrow = {}

    def list_asset(self, seller_id: str, asset_name: str, price: float):
        asset_id = f"asset_{hash(asset_name)}"
        listing = {
            "asset_id": asset_id,
            "seller_id": seller_id,
            "name": asset_name,
            "price": price,
            "status": "LISTED"
        }
        self.shadow.commit("imoxon.asset.listed", listing)
        return listing

    def initiate_transfer(self, asset_id: str, buyer_id: str, amount: float):
        # Lock in escrow
        self.escrow[asset_id] = {
            "buyer_id": buyer_id,
            "amount": amount,
            "status": "LOCKED"
        }
        self.event_bus.publish("imoxon.asset.escrow_locked", {"asset_id": asset_id, "buyer_id": buyer_id})
        return True

    def finalize_transfer(self, asset_id: str):
        if asset_id in self.escrow:
            data = self.escrow.pop(asset_id)
            data["status"] = "TRANSFERRED"
            self.shadow.commit("imoxon.asset.transferred", data)
            self.event_bus.publish("imoxon.asset.finalized", {"asset_id": asset_id})
            return True
        return False
