from typing import Dict, Any

class NetworkSecurityException(Exception):
    pass

class OrbanVPN:
    """
    Network Security Layer (Orban VPN):
    Enforces private encrypted tunnel (WireGuard) access.
    Blocks all public/unencrypted traffic.
    """
    def __init__(self):
        # In a real environment, this would interface with WireGuard/Kernel
        self.enforced = True

    def validate_connection(self, connection_context: Dict[str, Any]):
        """
        Verifies that the request is coming through the Orban VPN tunnel.
        Enforces full context check (tunnel, source_ip, node_id).
        """
        if not connection_context:
             raise NetworkSecurityException("ORBAN: Connection context is mandatory.")

        is_vpn = connection_context.get("is_vpn", False)
        tunnel_id = connection_context.get("tunnel_id")
        encryption_status = connection_context.get("encryption", "none")
        tunnel_type = connection_context.get("tunnel")

        if not is_vpn or tunnel_type != "orban":
            raise NetworkSecurityException("ORBAN: Public access blocked. Private Orban VPN tunnel required.")

        if not tunnel_id:
            raise NetworkSecurityException("ORBAN: Missing tunnel identity.")

        if encryption_status != "wireguard":
            raise NetworkSecurityException(f"ORBAN: Insecure encryption '{encryption_status}'. WireGuard required.")

        if not connection_context.get("source_ip") or not connection_context.get("node_id"):
            raise NetworkSecurityException("ORBAN: Incomplete network telemetry (IP/Node missing).")

        return True

orban = OrbanVPN()
