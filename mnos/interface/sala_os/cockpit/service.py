from typing import Dict, Any, List
from mnos.core.aig_tunnel.service import aig_tunnel
from mnos.core.aig_aegis.service import aig_aegis

class SalaCockpitService:
    """
    SALA Cockpit Service: Establishes ORBAN-secured WebSocket streams.
    Streams: live_folio, intent_stream, arrival_radar.
    """
    def connect_stream(self, stream_name: str, session_context: Dict[str, Any], connection_context: Dict[str, Any]):
        """
        Connects to a live operational stream with strict security.
        """
        # 1. Network Validation (ORBAN)
        aig_tunnel.validate_connection(connection_context)

        # 2. Identity & Mission Scope Validation
        aig_aegis.validate_session(session_context)

        # Check Mission Scope
        if session_context.get("mission_scope") != "V1":
             raise RuntimeError(f"COCKPIT: Access to stream '{stream_name}' denied. Scope 'V1' required.")

        print(f"[COCKPIT] Connected to secured stream: {stream_name}")
        return {"status": "CONNECTED", "stream": stream_name}

cockpit_service = SalaCockpitService()
