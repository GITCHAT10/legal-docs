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
    Converts validated geometry/BOQ into a locked supply chain order.
    """
    # 1. Hard Block Check (Fail-Closed)
    if "error" in boq:
        return {
            "status": "❌ HARD BLOCK",
            "reason": f"Sovereign Security Violation: {boq['error']}",
            "action": "Procurement Terminated"
        }

    # 2. Extract Quantities
    steel_tons = boq["quantities"]["steel_tons"]

    # 3. Simulate Alibaba Order Lock
    order_id = f"SXOS-W2-{uuid.uuid4().hex[:8].upper()}"

    shipment_details = {
        "order_id": order_id,
        "supplier": SUPPLIERS["steel"],
        "material": "Structural Steel Reinforcement",
        "quantity": f"{steel_tons} Tons",
        "lock_status": "LOCKED",
        "status": "PREPARING_FOR_SHIPMENT"
    }

    return {
        "status": "✅ WAVE 2 RELEASED",
        "event_id": str(uuid.uuid4()),
        "procurement": shipment_details,
        "total_commitment": f"{boq['currency']} {boq['total_estimate']:,}",
        "action": "Supply Chain Locked to Geometry"
    }
