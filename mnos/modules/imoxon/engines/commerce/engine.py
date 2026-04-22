class CommerceEngine:
    def __init__(self, shadow, events):
        self.shadow = shadow
        self.events = events
        self.stores = {} # store_id -> details

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
