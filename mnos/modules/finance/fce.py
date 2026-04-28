from decimal import Decimal, ROUND_HALF_UP
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, UTC
from enum import Enum

class TaxType(str, Enum):
    TOURISM_STANDARD = "TOURISM_STANDARD" # 17% TGST
    TRANSPORT = "TRANSPORT"               # 17% TGST (often same as tourism)
    FNB = "FNB"                           # 17% TGST
    RETAIL = "RETAIL"                     # 8% GST
    EXEMPT = "EXEMPT"                     # 0%

class FCEEngine:
    def __init__(self):
        self.ledger = []
        self.locked_rates = {"USD": Decimal("15.42")} # MVR

    def calculate_local_order(self,
                             base_price: Any,
                             category: str = "TOURISM_STANDARD",
                             green_tax_usd: Any = Decimal("0"),
                             locked_fx_rate: Any = Decimal("15.42"),
                             input_currency: str = "USD") -> dict:
        """
        MANDATORY MALDIVES BILLING RULE (MIRA COMPLIANT):
        Supports dual-currency extraction for TGST in USD (Tourism).
        1. base_price (in input_currency, usually USD)
        2. -> service_charge (10% if Tourism)
        3. -> subtotal = base + SC
        4. -> TGST/GST (on subtotal)
        5. -> + green tax (if applicable)
        6. -> = total (in input_currency)
        7. -> converted to MVR for ledger
        """
        # Ensure Decimal
        base_price = Decimal(str(base_price))
        green_tax_usd = Decimal(str(green_tax_usd))
        locked_fx_rate = Decimal(str(locked_fx_rate))

        # Quantize to 2 decimal places
        base_price = base_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 1. Resolve Rates
        is_tourism = category in [TaxType.TOURISM_STANDARD, TaxType.TRANSPORT, TaxType.FNB, "TOURISM", "RESORT_SUPPLY"]

        if is_tourism:
            tax_rate = Decimal("0.17")
            sc_rate = Decimal("0.10")
        elif category == TaxType.RETAIL:
            tax_rate = Decimal("0.08")
            sc_rate = Decimal("0.00")
        elif category == TaxType.EXEMPT:
            tax_rate = Decimal("0.00")
            sc_rate = Decimal("0.00")
        else:
            tax_rate = Decimal("0.08")
            sc_rate = Decimal("0.00")

        # 2. Service Charge
        service_charge = (base_price * sc_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        subtotal = base_price + service_charge

        # 3. TGST / GST
        tax_amt = (subtotal * tax_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 4. Green Tax (Honeymoon/Resort specific)
        green_tax = green_tax_usd.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total_input = subtotal + tax_amt + green_tax

        # 5. DUAL CURRENCY EXTRACTION (MIRA REQUIREMENT)
        # Tourism TGST must be reported/extracted in USD
        tgst_usd = tax_amt if input_currency == "USD" and is_tourism else Decimal("0")

        # 6. MVR LEDGER CALCULATION
        mvr_total = (total_input * locked_fx_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "transaction_id": uuid.uuid4().hex[:8],
            "base_usd": float(base_price) if input_currency == "USD" else 0,
            "base_mvr": float(base_price * locked_fx_rate) if input_currency == "USD" else float(base_price),
            "service_charge": float(service_charge),
            "subtotal": float(subtotal),
            "tax_rate": float(tax_rate),
            "tax_amount": float(tax_amt),
            "tgst_usd_extracted": float(tgst_usd),
            "green_tax": float(green_tax),
            "total_input_currency": float(total_input),
            "total_mvr": float(mvr_total),
            "fx_rate_locked": float(locked_fx_rate),
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
