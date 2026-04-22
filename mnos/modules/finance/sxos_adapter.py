from typing import Dict, Any
import uuid

# SXOS Supplier Mapping
SUPPLIERS = {
    "steel": "Alibaba Global Procurement",
    "concrete": "Male' ReadyMix Ltd",
    "blocks": "Local Island Supplier"
}

def release_sxos_wave_2(boq: Dict[str, Any]) -> Dict[str, Any]:
    """
    SXOS Wave 2: Validated Procurement Event.
    """
    if "error" in boq:
        return {"status": "❌ HARD BLOCK", "reason": boq["error"]}

    ledger = boq.get("fce_ledger", {})
    steel_tons = boq.get("quantities", {}).get("steel_tons", 0)

    order_id = f"SXOS-W2-{uuid.uuid4().hex[:8].upper()}"

    return {
        "status": "✅ WAVE 2 RELEASED",
        "procurement": {
            "order_id": order_id,
            "supplier": SUPPLIERS["steel"],
            "material": "Structural Steel Reinforcement",
            "quantity": f"{steel_tons} Tons"
        },
        "total_commitment": f"{ledger.get('currency', 'USD')} {ledger.get('total_commitment', 0):,}"
    }
