def calculate_maldives_tax(base_amount: float, apply_green_tax: bool = False, nights: int = 0):
    service_charge = base_amount * 0.10
    subtotal = base_amount + service_charge
    tgst = subtotal * 0.17

    green_tax = 0.0
    if apply_green_tax:
        green_tax = nights * 6.0 # standard USD 6

    total = subtotal + tgst + green_tax

    return {
        "base": base_amount,
        "service_charge": service_charge,
        "tgst": tgst,
        "green_tax": green_tax,
        "total": total
    }
