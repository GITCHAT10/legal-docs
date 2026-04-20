from typing import Dict, Any

def calculate_maldives_tax(base_amount: float, apply_green_tax: bool = False, nights: int = 0) -> Dict[str, float]:
    # 1. 10% Service Charge
    service_charge = base_amount * 0.10

    # 2. subtotal = Base + SC
    subtotal = base_amount + service_charge

    # 3. 17% TGST on (Base + SC)
    tgst = subtotal * 0.17

    # 4. Green Tax per pax/night (Mocking 1 pax for now, $6/night)
    green_tax = 6.0 * nights if apply_green_tax else 0.0

    total_amount = subtotal + tgst + green_tax

    return {
        "base_amount": base_amount,
        "service_charge": service_charge,
        "tgst": tgst,
        "green_tax": green_tax,
        "total_amount": total_amount
    }

def calculate_folio_charge(db: Any, folio_id: int, charge_data: Dict[str, Any]) -> Dict[str, float]:
    # Authoritative tax calculation for FCE
    # FCE should also check for locked exchange rate here if multi-currency is active
    return calculate_maldives_tax(
        charge_data["base_amount"],
        charge_data.get("apply_green_tax", False),
        charge_data.get("nights", 0)
    )
