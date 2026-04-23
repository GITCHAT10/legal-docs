from decimal import Decimal
import uuid
from .ledger_schema import LedgerEntry, FinancialTransaction

class FCEEngine:
    def __init__(self):
        self.ledger = []

    def calculate_local_order(self, base_price: Decimal, tax_type: str = "GGST") -> dict:
        tax_rate = Decimal("0.08") if tax_type == "GGST" else Decimal("0.17")
        service_charge = (base_price * Decimal("0.10")).quantize(Decimal("0.01"))
        tax_amt = ((base_price + service_charge) * tax_rate).quantize(Decimal("0.01"))
        total = base_price + service_charge + tax_amt
        return {"transaction_id": uuid.uuid4().hex[:8], "total": float(total), "base": float(base_price)}

    def calculate_milestone_release(self, milestone: str, data: dict):
        # Milestone Model: Award (10%), Port (40%), QC (20%), Acceptance (30%)
        total = Decimal(str(data["total_amount"]))
        rates = {"AWARD": 0.10, "PORT": 0.40, "QC": 0.20, "ACCEPTANCE": 0.30}
        release_amt = (total * Decimal(str(rates.get(milestone, 0)))).quantize(Decimal("0.01"))
        return {"milestone": milestone, "release_amount": float(release_amt), "status": "COMMITTED"}

    def price_order(self, amount: float):
        return self.calculate_local_order(Decimal(str(amount)))

    def calculate_isky_split(self, booking_amount: Decimal) -> dict:
        return {"setup_fee": 100.0, "net": float(booking_amount)}
