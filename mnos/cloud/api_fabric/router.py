from typing import Dict, Any

class FabricRouter:
    """
    API FABRIC: Routing Control Layer.
    Manages reroute flags for failover and node promotion.
    """
    def __init__(self):
        self.routes = {} # service_name -> {target_node, reroute_active}

    def set_reroute_flag(self, service_name: str, target_node: str, active: bool = True):
        self.routes[service_name] = {
            "target_node": target_node,
            "reroute_active": active
        }
        print(f"[FABRIC] Reroute flag {'SET' if active else 'CLEARED'} for {service_name} -> {target_node}")

    def get_route_destination(self, service_name: str) -> str:
        route = self.routes.get(service_name)
        if route and route["reroute_active"]:
            return route["target_node"]
        return "PRIMARY_CORE"

    def sync_failover_status(self, failover_status: dict):
        """
        Automatically reroutes if a node has been promoted.
        """
        if failover_status.get("is_promoted"):
            node_id = failover_status["last_event"].get("node_id")
            # Reroute critical services to the promoted node
            self.set_reroute_flag("finance_api", node_id)
            self.set_reroute_flag("mobility_api", node_id)
