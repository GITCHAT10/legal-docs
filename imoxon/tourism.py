from decimal import Decimal

class TourismEngine:
    def __init__(self, fce):
        self.fce = fce

    def book_experience(self, user_id: str, experience_type: str, pax: int, nights: int, base_price_per_pax: float):
        base_price = Decimal(str(base_price_per_pax)) * pax
        pricing = self.fce.calculate_order_total(base_price, is_tourism=True, pax=pax, nights=nights)

        booking = {
            "user_id": user_id,
            "type": experience_type,
            "pax": pax,
            "nights": nights,
            "pricing": pricing,
            "status": "CONFIRMED"
        }
        return booking
