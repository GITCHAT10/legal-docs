from decimal import Decimal, ROUND_HALF_UP
import uuid

class FCEEngine:
    def __init__(self):
        self.ledger = []
        self.locked_rates = {"USD": Decimal("15.42")} # MVR

    def calculate_local_order(self, base_price: Decimal, category: str = "RETAIL") -> dict:
        """
        MANDATORY MALDIVES BILLING RULE:
        Base Price + 10% Service Charge = subtotal
        TGST/GST applied on subtotal
        """
        # Quantize to 2 decimal places for currency
        base_price = base_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 1. 10% Service Charge
        service_charge = (base_price * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        subtotal = base_price + service_charge

        # 2. TGST (17%) or GST (8%)
        # Policy: 17% for tourism-linked, 8% for general retail
        tax_rate = Decimal("0.17") if category in ["TOURISM", "RESORT_SUPPLY"] else Decimal("0.08")
        tax_amt = (subtotal * tax_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total = subtotal + tax_amt

        return {
            "transaction_id": uuid.uuid4().hex[:8],
            "base": float(base_price),
            "service_charge": float(service_charge),
            "subtotal": float(subtotal),
            "tax_rate": float(tax_rate),
            "tax_amount": float(tax_amt),
            "total": float(total),
            "currency": "MVR"
        }

    def finalize_invoice(self, base_amount: float, category: str = "RETAIL"):
        return self.calculate_local_order(Decimal(str(base_amount)), category)

    def calculate_refund(self, original_invoice: dict):
        # Full reversal logic
        refund = original_invoice.copy()
        refund["total"] = -original_invoice["total"]
        refund["type"] = "REVERSAL"
        return refund

    def price_order(self, amount: float):
        return self.calculate_local_order(Decimal(str(amount)))

    def calculate_milestone_release(self, milestone: str, data: dict):
        total = Decimal(str(data["total_amount"]))
        rates = {"AWARD": 0.10, "PORT": 0.40, "QC": 0.20, "ACCEPTANCE": 0.30}
        release_amt = (total * Decimal(str(rates.get(milestone, 0)))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return {"milestone": milestone, "release_amount": float(release_amt), "status": "COMMITTED"}

    def calculate_isky_split(self, booking_amount: Decimal) -> dict:
        """
        iSKY Payout Split: 85% to Hub, 15% to Platform
        """
        platform_cut = (booking_amount * Decimal("0.15")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        hub_net = booking_amount - platform_cut
        return {
            "total": float(booking_amount),
            "hub_net": float(hub_net),
            "platform_cut": float(platform_cut),
            "currency": "MVR"
        }
