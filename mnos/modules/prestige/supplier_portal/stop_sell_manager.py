class StopSellManager:
    def __init__(self, shadow):
        self.shadow = shadow
        self.stop_sales = {}

    def apply_stop_sell(self, actor_ctx, product_id):
        self.stop_sales[product_id] = True
        self.shadow.commit("prestige.supplier.stop_sell_activated", actor_ctx["identity_id"], {
            "product_id": product_id,
            "reason": "SUPPLIER_IMMEDIATE_STOP"
        })
        return {"product_id": product_id, "status": "STOP_SELL_ACTIVE"}

    def is_stopped(self, product_id):
        return self.stop_sales.get(product_id, False)
