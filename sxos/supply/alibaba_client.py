import uuid
import random

class AlibabaMockClient:
    def search_products(self, query: str):
        return [
            {"id": f"ali_{uuid.uuid4().hex[:8]}", "name": f"{query} Premium", "price": random.uniform(10.0, 500.0), "moq": 10},
            {"id": f"ali_{uuid.uuid4().hex[:8]}", "name": f"{query} Bulk", "price": random.uniform(5.0, 200.0), "moq": 100}
        ]

    def create_order(self, product_id: str, quantity: int):
        return {
            "order_id": f"ali_ord_{uuid.uuid4().hex[:8]}",
            "status": "PLACED",
            "est_delivery_days": 15
        }
