class TenantManager:
    """
    Bucket A: MNO Controller.
    Segregates data at the Island level.
    """
    def __init__(self):
        self.islands = {}

    def get_island_context(self, island_id: str):
        return {"island_id": island_id, "region": "North Ari Atoll"}

tenant_manager = TenantManager()
