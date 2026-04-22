class SupplyEngine:
    def __init__(self, event_bus):
        self.event_bus = event_bus

    def trigger_restock(self, merchant_id: str, listing_id: str, amount: int):
        print(f"[SUPPLY] Triggering restock for Merchant {merchant_id}, Item {listing_id}")
        payload = {
            "merchant_id": merchant_id,
            "listing_id": listing_id,
            "amount": amount,
            "status": "ORDERED"
        }
        self.event_bus.publish("imoxon.supply.ordered", payload)
        return payload
