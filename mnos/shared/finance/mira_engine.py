from typing import Dict, Any, Optional
from mnos.shared.finance.rounding import round_bankers
from enum import Enum

class TaxProfile(str, Enum):
    TOURISM = "tourism"
    GENERAL = "general"

class IdentityTier(str, Enum):
    GUEST = "guest"
    CITIZEN = "citizen"
    WORK_PERMIT = "work_permit"

def calculate_mira_tax(amount: float, profile: TaxProfile) -> Dict[str, Any]:
    """
    Unified MIRA Tax Engine for MIG.

    TOURISM: 10% Service Charge + 17% TGST on (Base + SC)
    GENERAL: 8% GST on Base
    """
    if profile == TaxProfile.TOURISM:
        service_charge = round_bankers(amount * 0.10)
        subtotal = amount + service_charge
        tgst = round_bankers(subtotal * 0.17)
        return {
            "base": amount,
            "sc": service_charge,
            "tax": tgst,
            "tax_type": "TGST",
            "tax_rate": 0.17,
            "total": round_bankers(subtotal + tgst)
        }
    else:
        gst = round_bankers(amount * 0.08)
        return {
            "base": amount,
            "sc": 0.0,
            "tax": gst,
            "tax_type": "GST",
            "tax_rate": 0.08,
            "total": round_bankers(amount + gst)
        }

def route_settlement(amount: float, tier: IdentityTier) -> Dict[str, str]:
    """
    Routes settlement based on identity tier.
    """
    if tier == IdentityTier.GUEST:
        return {"currency": "USD", "gateway": "STRIPE/BML_USD"}
    else:
        return {"currency": "MVR", "gateway": "BML_MVR/DHIRAAGUPAY"}
