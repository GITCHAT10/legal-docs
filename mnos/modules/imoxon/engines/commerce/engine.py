class CommerceEngine:
    def __init__(self, fce, shadow, events):
        self.fce = fce
        self.shadow = shadow
        self.events = events
        self.stores = {}

    def onboard_vendor(self, vendor_data: dict):
        vendor_id = vendor_data.get("did")
        self.stores[vendor_id] = {
            "name": vendor_data.get("business_name"),
            "inventory": [],
            "type": "island_store"
        }
        self.shadow.record_action("vendor.onboarded", vendor_data)
        self.events.trigger("VENDOR_APPROVED", vendor_id)
        return True

    def create_listing(self, vendor_id: str, listing: dict):
        if vendor_id in self.stores:
            self.stores[vendor_id]["inventory"].append(listing)
            self.shadow.record_action("listing.created", listing)
            return True
        return False

    def process_order(self, user_id: str, listing_id: str, vendor_id: str, amount: float):
        # 1. Financial calculation strictly via FCE
        pricing = self.fce.price_order(amount)

        order = {
            "user": user_id,
            "listing": listing_id,
            "vendor": vendor_id,
            "pricing": pricing,
            "status": "PAID"
        }

        # 2. Immutable record
        self.shadow.record_action("order.completed", order)

        # 3. Side effects only after commit
        self.events.trigger("ORDER_CREATED", order)
        return order
