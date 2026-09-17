class ConstructionSupplyChainRouter:
    """
    CONSTRUCTION_SUPPLY_CHAIN_ROUTER (RC1-PRODUCTION-BRIDGE)
    Routes construction material requests from resorts to verified suppliers.
    """
    def __init__(self, procurement):
        self.procurement = procurement

    def route_material_request(self, actor_ctx: dict, resort_id: str, materials: list):
        # Auto-initiate procurement pipeline
        total_est = sum(m.get("price", 0) for m in materials)
        return self.procurement.create_purchase_request(actor_ctx, materials, total_est)
