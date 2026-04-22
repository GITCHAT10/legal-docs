from typing import Dict, Any

class NetworkSecurityException(Exception):
    pass

class AIGTunnelVPN:
    """
    Network Security Layer (AIGTunnel):
    Enforces private encrypted tunnel (WireGuard) access.
    Blocks all public/unencrypted traffic.
    """
    def __init__(self):
        # In a real environment, this would interface with WireGuard/Kernel
        self.enforced = True

    def validate_connection(self, connection_context: Dict[str, Any]):
        """
        Verifies that the request is coming through the AIGTunnel tunnel.
        Enforces full context check (tunnel, source_ip, node_id).
        """
        if not connection_context:
             raise NetworkSecurityException("AIG_TUNNEL: Connection context is mandatory.")

        is_vpn = connection_context.get("is_vpn", False)
        tunnel_id = connection_context.get("tunnel_id")
        encryption_status = connection_context.get("encryption", "none")
        tunnel_type = connection_context.get("tunnel")

        if not is_vpn or tunnel_type != "aig_tunnel":
            raise NetworkSecurityException("AIG_TUNNEL: Public access blocked. Private AIGTunnel tunnel required.")

        if not tunnel_id:
            raise NetworkSecurityException("AIG_TUNNEL: Missing tunnel identity.")

        if encryption_status != "wireguard":
            raise NetworkSecurityException(f"AIG_TUNNEL: Insecure encryption '{encryption_status}'. WireGuard required.")

        if not connection_context.get("source_ip") or not connection_context.get("node_id"):
            raise NetworkSecurityException("AIG_TUNNEL: Incomplete network telemetry (IP/Node missing).")

        return True

aig_tunnel = AIGTunnelVPN()
