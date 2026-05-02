import time
from datetime import datetime, UTC
from typing import Dict, Any, Literal, Optional
import os

ChannelType = Literal["PUBLIC", "DIRECT", "SOVEREIGN", "OTA_CRAWLER"]

class SilentShieldEdge:
    """
    SILENT SHIELD Edge Layer Simulation (Cloudflare Worker Logic).
    Routes requests by channel, enforces rate limits, and logs to SHADOW.
    """
    def __init__(self, shadow, events):
        self.shadow = shadow
        self.events = events
        self.rate_store = {} # (ip, channel) -> [timestamps]

        # Balanced limits for production and testing
        self.limits = {
            "PUBLIC":       {"rpm": 100, "burst": 20},
            "DIRECT":       {"rpm": 500, "burst": 100},
            "SOVEREIGN":    {"rpm": 2000, "burst": 500},
            "OTA_CRAWLER":  {"rpm": 20, "burst": 5}
        }

    def process_request(self, ip: str, ua: str, path: str, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """Simulates the edge fetch event."""
        # 1. Channel Classification
        channel = self._classify_channel(ua, path, auth_token)

        # 2. Rate Limiting
        if self._is_rate_limited(ip, channel):
            # NO COMMIT here if not in authorized context, or use internal commit
            return {"status": 429, "message": "Rate limit exceeded. Retry later.", "channel": channel}

        # 3. Log to SHADOW
        # In a real edge, this is async and uses service token
        self.shadow.commit("shield.request_processed", "SYSTEM", {
            "ip": ip,
            "channel": channel,
            "path": path,
            "ua": ua
        })

        return {"status": 200, "channel": channel}

    def _classify_channel(self, ua: str, path: str, auth_token: str) -> ChannelType:
        if auth_token == "SOVEREIGN_TOKEN": return "SOVEREIGN"
        if "/mig-portal/" in path: return "DIRECT"
        if any(bot in (ua or "").lower() for bot in ["bot", "crawler", "scrape", "spider"]): return "OTA_CRAWLER"
        return "PUBLIC"

    def _is_rate_limited(self, ip: str, channel: str) -> bool:
        if os.environ.get("DISABLE_SHIELD_RATE_LIMIT") == "1":
            return False

        key = (ip, channel)
        now = time.time()

        if key not in self.rate_store:
            self.rate_store[key] = []

        # Clean old timestamps (1 minute window)
        self.rate_store[key] = [t for t in self.rate_store[key] if now - t < 60]

        limit = self.limits.get(channel, self.limits["PUBLIC"])
        if len(self.rate_store[key]) >= limit["rpm"]:
            return True

        self.rate_store[key].append(now)
        return False
