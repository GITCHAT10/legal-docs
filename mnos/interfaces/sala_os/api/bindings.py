from typing import Dict, Any
from mnos.core.events.service import events
from mnos.modules.fce.service import fce
from mnos.modules.exmail.service import exmail_authority

class SalaApiBridge:
    """
    SALA-OS API Binding Layer.
    Maps UI endpoints to MNOS Core authorities.
    """
    def __init__(self):
        self.bindings = {
            "arrivals": {"endpoint": "/events/arrivals", "source": "EVENTS"},
            "rooms": {"endpoint": "/rooms/status", "source": "CORE"},
            "folios": {"endpoint": "/fce/folios", "source": "FCE"},
            "housekeeping": {"endpoint": "/ops/housekeeping", "source": "OPERATIONS"},
            "transfers": {"endpoint": "/transport/live", "source": "ATC_TOWER"},
            "guest": {"endpoint": "/guest/profile", "source": "CRMLAB"},
            "mail": {"endpoint": "/exmail/inbox", "source": "EXMAIL"}
        }

    def fetch_data(self, key: str, session_context: Dict[str, Any], params: Dict[str, Any] = None):
        """Hardened data fetch: requires AEGIS signed session."""
        from mnos.core.security.aegis import aegis
        aegis.require_signed_session_context(session_context)

        if key not in self.bindings:
            raise ValueError(f"Unknown API binding: {key}")

        source = self.bindings[key]["source"]
        print(f"[SALA-API] Fetching {key} from {source}...")

        # Simulated source resolution
        if source == "EVENTS":
            return {"status": "LIVE", "events": []}
        elif source == "FCE":
            return {"folios": []}
        elif source == "EXMAIL":
            return {"inbox": []}

        return {"status": "OK", "data": {}}

sala_api = SalaApiBridge()
