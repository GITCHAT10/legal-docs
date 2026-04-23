class FranchiseEngine:
    def __init__(self, fce, shadow):
        self.fce = fce
        self.shadow = shadow
        self.hubs = {} # hub_id -> stores[]

    def create_atoll_hub(self, hub_id: str, location: str):
        self.hubs[hub_id] = {"location": location, "stores": []}
        self.shadow.commit("hub.created", {"hub_id": hub_id, "location": location})

    def process_payout_split(self, amount: float, vendor_id: str):
        pricing = self.fce.price_order(amount)
        # Fix: Mismatch in dictionary keys from FCE pricing output
        # FCE returns {'transaction_id', 'total', 'base'}
        # But we need platform fee (which is total - base)
        vendor_net = pricing["base"]
        platform_fee = pricing["total"] - pricing["base"]

        split = {
            "vendor_id": vendor_id,
            "total": amount,
            "vendor_net": vendor_net,
            "platform_fee": platform_fee
        }
        self.shadow.commit("payout.split", split)
        return split
