class MerchantEngine:
    def __init__(self):
        self.inventory = {} # listing_id -> stock

    def update_stock(self, listing_id: str, quantity: int):
        self.inventory[listing_id] = quantity
        print(f"[MERCHANT] Updated stock for {listing_id}: {quantity}")

    def decrement_stock(self, listing_id: str, amount: int = 1):
        if self.inventory.get(listing_id, 0) >= amount:
            self.inventory[listing_id] -= amount
            return True
        return False
