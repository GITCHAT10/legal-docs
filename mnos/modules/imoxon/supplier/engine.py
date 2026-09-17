class SupplierManager:
    def __init__(self, guard, events):
        self.guard = guard
        self.events = events
        self.suppliers = {}

    def register_node(self, actor_ctx: dict, node_data: dict):
        return self.guard.execute_sovereign_action(
            "imoxon.supplier.register",
            actor_ctx,
            self._internal_register,
            node_data
        )

    def _internal_register(self, data):
        supplier_id = data.get("id")
        self.suppliers[supplier_id] = data
        self.events.publish("SUPPLIER_NODE_REGISTERED", data)
        return {"id": supplier_id, "status": "ACTIVE"}
