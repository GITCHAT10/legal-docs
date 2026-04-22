class FranchiseEngine:
    def __init__(self, fce, shadow):
        self.fce = fce
        self.shadow = shadow
        self.hubs = {} # hub_id -> stores[]

    def create_atoll_hub(self, hub_id: str, location: str):
        self.hubs[hub_id] = {"location": location, "stores": []}
        self.shadow.record_action("hub.created", {"hub_id": hub_id, "location": location})

    def process_payout_split(self, amount: float, vendor_id: str):
        pricing = self.fce.price_order(amount)
        platform_fee = pricing["service_charge"]
        vendor_net = pricing["base_price"]

        split = {
            "vendor_id": vendor_id,
            "total": amount,
            "vendor_net": vendor_net,
            "platform_fee": platform_fee
        }
        self.shadow.record_action("payout.split", split)
        return split
