from typing import Dict, List
from enum import Enum

class DeploymentTier(Enum):
    MALE_HQ = "CORE_HQ"
    ATOLL_HUB = "REGIONAL_HUB"
    ISLAND_EDGE = "LOCAL_EDGE"

class AigAirCloudTopology:
    """
    AIG AIR CLOUD: Sovereign Deployment Topology.
    Defines infrastructure nodes and sync relationships.
    """
    def __init__(self):
        self.nodes = {
            "MALE-CORE-01": {"tier": DeploymentTier.MALE_HQ, "status": "ONLINE", "region": "K.Male"},
            "SALA-EDGE-01": {"tier": DeploymentTier.ISLAND_EDGE, "status": "ONLINE", "region": "ADh.Omadhoo"}
        }

    def get_sync_path(self, source_node: str, target_node: str) -> List[str]:
        # Simple topology routing: LOCAL_EDGE -> REGIONAL_HUB (optional) -> CORE_HQ
        return ["LOCAL_CACHE", "EDGE_WAL_QUEUE", "CORE_SYNC_COMMIT"]

    def get_node_config(self, node_id: str) -> dict:
        node = self.nodes.get(node_id, {})
        return {
            "node_id": node_id,
            "tier": node.get("tier", DeploymentTier.ISLAND_EDGE).value,
            "sync_mode": "WAL_IDEMPOTENT",
            "compute_spec": "NVIDIA_T4_EDGE" if node.get("tier") == DeploymentTier.ISLAND_EDGE else "NVIDIA_A100_CLUSTER"
        }
