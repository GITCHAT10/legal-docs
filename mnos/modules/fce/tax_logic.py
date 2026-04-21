from datetime import date, datetime
from typing import Dict, Any

def calculate_maldives_tax(base_amount: float, business_date: date, apply_green_tax: bool = False, nights: int = 0) -> Dict[str, float]:
    """
    Sovereign Tax Logic (Genesis Root).
    Implements deterministic transitions for TGST and Green Tax.
    """
    # 1. 10% Service Charge (Constant)
    service_charge = base_amount * 0.10

    # 2. subtotal = Base + SC
    subtotal = base_amount + service_charge

    # 3. 17% TGST (Effective July 1, 2025)
    # Prior to that it was 16% (or 12% in earlier eras, but we track 2025+ here)
    tgst_rate = 0.17 if business_date >= date(2025, 7, 1) else 0.16
    tgst = subtotal * tgst_rate

    # 4. Green Tax (Effective Jan 1, 2025: $12 per day for resorts)
    # Under-2 exemption check would happen here if pax data provided
    daily_green_tax_rate = 12.0 if business_date >= date(2025, 1, 1) else 6.0
    green_tax = daily_green_tax_rate * nights if apply_green_tax else 0.0

    total_amount = subtotal + tgst + green_tax

    return {
        "base_amount": base_amount,
        "service_charge": service_charge,
        "tgst": tgst,
        "green_tax": green_tax,
        "total_amount": round(total_amount, 2),
        "tgst_rate": tgst_rate,
        "green_tax_rate": daily_green_tax_rate
    }

def calculate_folio_charge(db: Any, folio_id: int, charge_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Authoritative inter-module call for FCE.
    Uses the business_date from charge_data or defaults to current date.
    """
    biz_date = charge_data.get("business_date")
    if isinstance(biz_date, str):
        biz_date = date.fromisoformat(biz_date)
    elif not biz_date:
        biz_date = date.today()

    return calculate_maldives_tax(
        charge_data["base_amount"],
        biz_date,
        charge_data.get("apply_green_tax", False),
        charge_data.get("nights", 0)
    )
