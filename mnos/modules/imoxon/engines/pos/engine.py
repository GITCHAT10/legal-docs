class POSEngine:
    def __init__(self, guard, fce, shadow, events):
        self.guard = guard
        self.fce = fce
        self.shadow = shadow
        self.events = events

    def update_stock(self, actor_ctx: dict, stock_data: dict):
        return self.guard.execute_sovereign_action(
            "imoxon.pos.update_stock",
            actor_ctx,
            self._internal_update_stock,
            stock_data
        )

    def _internal_update_stock(self, data: dict):
        # POS stock update side effect
        self.events.publish("pos.stock_updated", data)
        return {"status": "SYNCED", "count": data.get("count")}
