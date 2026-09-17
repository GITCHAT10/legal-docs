import uuid
from datetime import datetime, UTC

class MaldivesRestaurantEngine:
    """
    AI-Powered Restaurant Management Engine for Maldives.
    Features: Voice Order AI, Table Management, AI Demand Forecasting,
    and integrated Offline POS (via BPE).
    Compliance: Maldives Tax Logic (10% SC + 17% TGST).
    """
    def __init__(self, core, bpe):
        self.core = core
        self.bpe = bpe # Bubble POS Engine (Stocky POS Logic)
        self.restaurants = {}
        self.orders = {}
        self.voice_intent_map = {
            "order": "CREATE_ORDER",
            "bill": "GENERATE_BILL",
            "status": "CHECK_STATUS"
        }

    def register_restaurant(self, actor_ctx: dict, rest_data: dict):
        return self.core.execute_commerce_action(
            "restaurant.register",
            actor_ctx,
            self._internal_register,
            rest_data
        )

    def _internal_register(self, data):
        rest_id = f"REST-{uuid.uuid4().hex[:6].upper()}"
        restaurant = {
            "id": rest_id,
            "name": data.get("name"),
            "island": data.get("island"),
            "tables": data.get("tables", 10),
            "status": "ACTIVE"
        }
        self.restaurants[rest_id] = restaurant
        return restaurant

    def process_voice_order(self, actor_ctx: dict, rest_id: str, transcript: str):
        """
        AI Voice Order Processing Simulation.
        Transcript examples: "I want to order a fish curry", "Give me the bill"
        """
        intent = "UNKNOWN"
        for keyword, mapped_intent in self.voice_intent_map.items():
            if keyword in transcript.lower():
                intent = mapped_intent
                break

        if intent == "CREATE_ORDER":
            return self.create_order(actor_ctx, rest_id, {"items": [{"name": "Voice Item", "price": 150.0}]})
        elif intent == "GENERATE_BILL":
            return {"status": "BILLING_INITIATED", "message": "Waiter is bringing your bill."}

        return {"status": "AI_UNCERTAIN", "message": "Could you please repeat that?"}

    def create_order(self, actor_ctx: dict, rest_id: str, order_data: dict):
        return self.core.execute_commerce_action(
            "restaurant.order.create",
            actor_ctx,
            self._internal_create_order,
            rest_id, order_data, actor_ctx
        )

    def _internal_create_order(self, rest_id, data, actor_ctx):
        items = data.get("items", [])
        base_total = sum(item.get("price", 0) for item in items)

        # Integrate with BPE for inventory/billing
        invoice = self.bpe.create_invoice(rest_id, {"amount": base_total, "order_id": f"R-{uuid.uuid4().hex[:4]}"})

        order = {
            "order_id": f"ORD-REST-{uuid.uuid4().hex[:6].upper()}",
            "restaurant_id": rest_id,
            "customer_id": actor_ctx.get("identity_id"),
            "items": items,
            "pricing": invoice["pricing"], # FCE Hardened Logic via BPE
            "status": "PLACED",
            "timestamp": datetime.now(UTC).isoformat()
        }
        self.orders[order["order_id"]] = order
        self.core.events.publish("restaurant.order_placed", order)
        return order

    def get_ai_demand_forecast(self, rest_id: str):
        """
        AI Analysis Simulation (Historical data + Seasonality).
        """
        # Logic: High demand during Ramadan or Peak Tourist Season
        return {
            "restaurant_id": rest_id,
            "forecast": "HIGH",
            "recommended_stock": ["Fresh Fish", "Rice", "Spices"],
            "confidence": 0.89
        }
