from decimal import Decimal

class FCEAdapter:
    def __init__(self, engine):
        self.engine = engine

    def price_order(self, base_price: float):
        return self.engine.calculate_local_order(Decimal(str(base_price)))

    def authorize_payment(self, amount: float):
        # Implementation of payment authorization
        print(f"[FCE] Authorized payment of {amount}")
        return True

    def calculate_isky_split(self, booking_amount: float):
        return self.engine.calculate_isky_commission(Decimal(str(booking_amount)))
