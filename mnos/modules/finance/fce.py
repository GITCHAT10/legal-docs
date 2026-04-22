from decimal import Decimal
import uuid
from .ledger_schema import LedgerEntry, FinancialTransaction

class FCEEngine:
    """
    Financial Control Engine (FCE): Authority for local Maldives economy.
    MIRA Compliant with double-entry ledger integration.
    """
    SERVICE_CHARGE = Decimal("0.10")
    TGST = Decimal("0.17")
    GGST = Decimal("0.08")
    COMMISSION_RATE = Decimal("0.05")

    def __init__(self):
        self.ledger = []

    def calculate_local_order(self, base_price: Decimal, tax_type: str = "GGST") -> dict:
        service_charge_amt = (base_price * self.SERVICE_CHARGE).quantize(Decimal("0.01"))
        subtotal = base_price + service_charge_amt

        tax_rate = self.TGST if tax_type == "TGST" else self.GGST
        tax_amt = (subtotal * tax_rate).quantize(Decimal("0.01"))
        total = subtotal + tax_amt

        # 1. Create Financial Transaction
        tid = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        txn = FinancialTransaction(
            transaction_id=tid,
            amount_base=base_price,
            amount_tax=tax_amt,
            amount_total=total,
            tax_type=tax_type
        )

        # 2. Create Double-Entry records
        # Debit: Cash/Receivable
        txn.entries.append(LedgerEntry(
            entry_id=f"ENT-{uuid.uuid4().hex[:4]}",
            transaction_id=tid,
            account_code="1001-ASSET-CASH",
            debit=total,
            description=f"Payment received for {tid}"
        ))
        # Credit: Revenue
        txn.entries.append(LedgerEntry(
            entry_id=f"ENT-{uuid.uuid4().hex[:4]}",
            transaction_id=tid,
            account_code="4001-REVENUE-SALES",
            credit=base_price + service_charge_amt,
            description="Sales revenue"
        ))
        # Credit: GST Payable (MIRA)
        txn.entries.append(LedgerEntry(
            entry_id=f"ENT-{uuid.uuid4().hex[:4]}",
            transaction_id=tid,
            account_code=f"2001-LIAB-{tax_type}-PAYABLE",
            credit=tax_amt,
            tax_type=tax_type,
            tax_rate=tax_rate,
            description=f"{tax_type} collected for MIRA"
        ))

        self.ledger.append(txn)

        return {
            "transaction_id": tid,
            "base_price": float(base_price),
            "service_charge": float(service_charge_amt),
            "subtotal": float(subtotal),
            "tax": float(tax_amt),
            "total": float(total),
            "ledger_summary": f"{len(txn.entries)} entries recorded"
        }

    def price_order(self, amount: float):
        return self.calculate_local_order(Decimal(str(amount)))

    def calculate_isky_split(self, booking_amount: Decimal) -> dict:
        setup_fee = Decimal("100.00")
        commission = (booking_amount * self.COMMISSION_RATE).quantize(Decimal("0.01"))
        return {
            "setup_fee": float(setup_fee),
            "commission": float(commission),
            "net_payout": float(booking_amount - commission)
        }
