from decimal import Decimal

class FCEAdapter:
    def __init__(self, engine):
        self.engine = engine

    def price_order(self, base_price: float, category: str = "RETAIL"):
        return self.engine.calculate_local_order(Decimal(str(base_price)), category=category)

    def authorize_payment(self, amount: float):
        print(f"[FCE] Authorized payment of {amount}")
        return True

    def calculate_isky_split(self, booking_amount: float):
        # Fix: Ensure this matches the core engine method name
        return self.engine.calculate_isky_split(Decimal(str(booking_amount)))
