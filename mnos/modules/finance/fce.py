from decimal import Decimal, ROUND_HALF_UP
import uuid
from typing import Dict, Any
from datetime import datetime, UTC

class FCEEngine:
    def __init__(self):
        self.ledger = []
        self.locked_rates = {"USD": Decimal("15.42")} # MVR

    def calculate_local_order(self, base_price: Decimal, category: str = "RETAIL", pax: int = 0, nights: int = 0) -> dict:
        """
        MANDATORY MALDIVES BILLING RULE (RC1_HARDENED):
        Base Price + 10% Service Charge = subtotal
        TGST/GST applied on subtotal
        + Green Tax ($6/pax/night) if tourism
        """
        # Quantize to 2 decimal places for currency
        base_price = base_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 1. 10% Service Charge
        service_charge = (base_price * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        subtotal = base_price + service_charge

        # 2. TGST (17%) or GST (8%)
        tax_rate = Decimal("0.17") if category in ["TOURISM", "RESORT_SUPPLY"] else Decimal("0.08")
        tax_amt = (subtotal * tax_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 3. Green Tax ($6 USD equivalent)
        green_tax = Decimal("0.00")
        if category == "TOURISM" and pax > 0 and nights > 0:
             # USD to MVR fixed at 15.42
             green_tax = (Decimal("6.00") * Decimal(str(pax)) * Decimal(str(nights)) * self.locked_rates["USD"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total = subtotal + tax_amt + green_tax

        return {
            "transaction_id": uuid.uuid4().hex[:8],
            "base": float(base_price),
            "service_charge": float(service_charge),
            "subtotal": float(subtotal),
            "tax_rate": float(tax_rate),
            "tax_amount": float(tax_amt),
            "green_tax": float(green_tax),
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

    def void_transaction(self, original_tx_id: str):
        # Implementation of REVERSAL flow
        return {"original_id": original_tx_id, "status": "VOIDED", "timestamp": datetime.now(UTC).isoformat()}

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

    def process_clearing_settlement(self, amount: float, parties: dict):
        """
        N-DEOS Financial Clearing: Multi-party T+1 settlement.
        Parties: {resort, supplier, logistics, tax}
        """
        amt = Decimal(str(amount))
        # FX Lock simulated
        settlement = {
            "clearing_id": uuid.uuid4().hex[:8],
            "timestamp": datetime.now(UTC).isoformat(),
            "status": "PENDING_T+1",
            "distributions": {k: float(amt * Decimal(str(v))) for k, v in parties.items()}
        }
        return settlement

    def calculate_installment_plan(self, total_amount: float, months: int) -> dict:
        """
        iMOXON Installment Flow: Splits payment into scheduled monthly chunks.
        """
        total = Decimal(str(total_amount))
        monthly_base = (total / Decimal(str(months))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Adjust last installment for rounding drift
        last_installment = total - (monthly_base * Decimal(str(months - 1)))

        schedule = []
        for i in range(1, months):
            schedule.append({
                "period": i,
                "amount": float(monthly_base),
                "status": "SCHEDULED"
            })

        schedule.append({
            "period": months,
            "amount": float(last_installment),
            "status": "SCHEDULED"
        })

        return {
            "plan_id": f"CRED-{uuid.uuid4().hex[:6].upper()}",
            "total_amount": float(total),
            "months": months,
            "monthly_amount": float(monthly_base),
            "schedule": schedule,
            "status": "ACTIVE"
        }

    def calculate_payout(self, order_total: float, commission_rate: float = 0.05) -> dict:
        """
        iMOXON Payout Flow: Calculates net payout after platform commission and taxes.
        """
        total = Decimal(str(order_total))
        commission = (total * Decimal(str(commission_rate))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Taxes on commission (e.g., 8% GST on the service provided by the platform)
        commission_tax = (commission * Decimal("0.08")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        net_payout = total - commission - commission_tax

        return {
            "payout_id": f"PAY-{uuid.uuid4().hex[:6].upper()}",
            "order_total": float(total),
            "commission": float(commission),
            "commission_tax": float(commission_tax),
            "net_payout": float(net_payout),
            "scheduled_date": datetime.now(UTC).isoformat(),
            "status": "SCHEDULED"
        }

class FCEHardenedEngine:
    """
    FCE Hardened Engine: Legacy wrapper for Phase 1.
    """
    def __init__(self, shadow_ledger):
        self.shadow = shadow_ledger
        self.engine = FCEEngine()
        self.escrows = {}

    def calculate_maldives_order(self, base_price: Decimal):
        return self.engine.calculate_local_order(base_price, "RESORT_SUPPLY")

    def create_escrow(self, actor_id: str, amount: float, ref_id: str):
        escrow_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
        self.escrows[escrow_id] = {
            "amount": amount,
            "ref_id": ref_id,
            "status": "LOCKED",
            "released_amount": 0.0
        }
        self.shadow.commit("fce.escrow_locked", actor_id, {"escrow_id": escrow_id, "amount": amount})
        return escrow_id

    def release_milestone(self, actor_id: str, escrow_id: str, milestone_pct: int):
        milestone_map = {10: "AWARD", 40: "PORT", 20: "QC", 30: "ACCEPTANCE"}
        milestone_name = milestone_map.get(milestone_pct)

        escrow = self.escrows.get(escrow_id)
        release_res = self.engine.calculate_milestone_release(milestone_name, {"total_amount": escrow["amount"]})

        escrow["released_amount"] += release_res["release_amount"]
        self.shadow.commit("fce.milestone_released", actor_id, {
            "escrow_id": escrow_id,
            "percentage": milestone_pct,
            "amount": release_res["release_amount"]
        })
        return release_res["release_amount"]
