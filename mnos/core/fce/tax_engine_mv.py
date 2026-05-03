from decimal import Decimal, ROUND_HALF_UP
from mnos.core.fce.models import FCEPriceBreakdown

def calculate_maldives_tax(base_price: float, currency: str = "USD") -> FCEPriceBreakdown:
    """
    Maldives billing rule v1.1:
    Base Price
    + 10% Service Charge
    = Taxable Subtotal
    + 17% TGST on Taxable Subtotal
    = Customer Total
    """
    if currency not in ["USD", "MVR"]:
        raise ValueError(f"Unsupported currency: {currency}")

    base = Decimal(str(base_price))

    service_charge = (base * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    taxable_subtotal = base + service_charge
    tgst = (taxable_subtotal * Decimal("0.17")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    customer_total = taxable_subtotal + tgst

    return FCEPriceBreakdown(
        base_price=float(base),
        service_charge=float(service_charge),
        taxable_subtotal=float(taxable_subtotal),
        tgst=float(tgst),
        customer_total=float(customer_total),
        currency=currency
    )
