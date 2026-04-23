class FoodEngine:
    def __init__(self, commerce, fce, shadow, events):
        self.commerce = commerce
        self.fce = fce
        self.shadow = shadow
        self.events = events

    def place_order(self, user_id: str, restaurant_id: str, items: list):
        base_price = sum(item["price"] for item in items)
        pricing = self.fce.price_order(base_price)

        order = {
            "user_id": user_id,
            "restaurant_id": restaurant_id,
            "items": items,
            "pricing": pricing,
            "status": "ORDERED"
        }

        self.shadow.commit("food.order.created", order)
        self.events.publish("ORDER_CREATED", order)
        return order
