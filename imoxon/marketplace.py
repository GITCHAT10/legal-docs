class MarketplaceEngine:
    def __init__(self):
        self.listings = {}
        self.coupons = {
            "SAVE10": 10.0,
            "WELCOME20": 20.0
        }

    def add_listing(self, listing_id: str, details: dict):
        self.listings[listing_id] = details
        return True

    def validate_coupon(self, code: str) -> float:
        return self.coupons.get(code, 0.0)

    def get_listings(self):
        return self.listings
