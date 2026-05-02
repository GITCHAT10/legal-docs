from fastapi import Request, HTTPException, Depends
from typing import Literal, Dict, Any, List, Optional
from pydantic import BaseModel

ChannelType = Literal["PUBLIC", "DIRECT", "SOVEREIGN", "OTA_CRAWLER"]

class VisibilityAsset(BaseModel):
    id: str
    name: str
    tier: str # BASE, ENHANCED, ALPHA
    bundle_eligible: bool = False
    price_mvr: float

class TierGateResponse(BaseModel):
    status: str
    tier: str
    data: Optional[Dict] = None
    message: Optional[str] = None

class TierGate:
    """
    SILENT SHIELD: Inventory Visibility Enforcement.
    Contract-safe, parity-compliant gating.
    """
    VISIBILITY_MAP = {
        "PUBLIC":       {"allowed": ["BASE"], "bundle": False},
        "DIRECT":       {"allowed": ["BASE", "ENHANCED"], "bundle": True},
        "SOVEREIGN":    {"allowed": ["BASE", "ENHANCED", "ALPHA"], "bundle": True},
        "OTA_CRAWLER":  {"allowed": ["BASE"], "bundle": False}
    }

    @staticmethod
    def apply_gate(channel: ChannelType, asset_tier: str, bundle_requested: bool = False) -> Dict[str, Any]:
        config = TierGate.VISIBILITY_MAP.get(channel, TierGate.VISIBILITY_MAP["PUBLIC"])

        # 1. Tier Check
        if asset_tier not in config["allowed"]:
            return {
                "status": "LIMITED_INVENTORY",
                "tier": "BASE",
                "message": "Premium inventory available via direct channels."
            }

        # 2. Bundle Eligibility Check (Parity Safety)
        if bundle_requested and not config["bundle"]:
            return {
                "status": "ROOM_ONLY",
                "tier": asset_tier,
                "message": "Bundled packages available on direct booking channels."
            }

        return {"status": "AUTHORIZED"}

def get_channel(request: Request) -> ChannelType:
    """Extracts classified channel from edge-injected header."""
    return request.headers.get("X-Channel-Type", "PUBLIC")
