from typing import Dict, Any

class NodeRegistry:
    """
    AEGIS Node Registry (FORTRESS): Governs same-cloud logically isolated nodes.
    Used by API Airlock for cross-tenant validation.
    """
    def __init__(self):
        # Ed25519 public keys would be stored here
        self._nodes = {
            "hms-resort-01": {
                "org_id": "MIG-SALA-HOTELS",
                "role": "INTERNAL_HMS",
                "public_key": "ed25519:hms_v1_key_placeholder",
                "allowed_scopes": ["rfq:create", "quotes:read", "order:create", "delivery:confirm"]
            },
            "imoxon-market-01": {
                "org_id": "MIG-MARKETPLACE",
                "role": "EXTERNAL_PROCUREMENT",
                "public_key": "ed25519:imoxon_v1_key_placeholder",
                "allowed_scopes": ["quote:create", "shipment:update"]
            }
        }

    def get_node(self, node_id: str) -> Dict[str, Any]:
        return self._nodes.get(node_id)

    def validate_scope(self, node_id: str, scope: str) -> bool:
        node = self.get_node(node_id)
        if not node:
            return False
        return scope in node["allowed_scopes"]

node_registry = NodeRegistry()
