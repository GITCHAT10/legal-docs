from decimal import Decimal, ROUND_HALF_UP
import uuid
from typing import Dict, Any, List

class UTFCESplitEngine:
    def __init__(self, fce_core, shadow):
        self.fce = fce_core
        self.shadow = shadow
        self.quotes = {}

    def create_quote(self, trace_id: str, base_amount: Decimal, category: str = "TRANSPORT", is_public_subsidy: bool = False) -> Dict:
        """
        Creates a quote with mandatory ESG/CSR USD 1 split and Maldives tax rules.
        """
        # Ensure base_amount is Decimal
        if not isinstance(base_amount, Decimal):
            base_amount = Decimal(str(base_amount))

        # 1. Standard Maldives Tax Calculation
        tax_calc = self.fce.calculate_local_order(base_amount, category)

        # 2. ESG/CSR Fee (USD 1 = MVR 15.42, split 50/50)
        esg_csr_total_mvr = Decimal("15.42")

        total_mvr = Decimal(str(tax_calc["total"])) + esg_csr_total_mvr

        quote = {
            "quote_id": str(uuid.uuid4()),
            "trace_id": trace_id,
            "base_amount": float(base_amount),
            "service_charge": tax_calc["service_charge"],
            "tax_amount": tax_calc["tax_amount"],
            "esg_csr_fee": float(esg_csr_total_mvr),
            "total_amount": float(total_mvr),
            "is_locked": False,
            "is_public_subsidy": is_public_subsidy
        }

        self.quotes[quote["quote_id"]] = quote
        return quote

    def prepare_split(self, quote_id: str, booking_source: str = None) -> List[Dict]:
        """
        Prepares ledger splits for the quote.
        """
        quote = self.quotes.get(quote_id)
        if not quote:
            raise ValueError("Quote not found")

        splits = []
        total = Decimal(str(quote["total_amount"]))

        # ESG/CSR Splits
        esg_csr_fee = Decimal(str(quote["esg_csr_fee"]))
        esg_share = (esg_csr_fee / 2).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        csr_share = esg_csr_fee - esg_share

        splits.append({"ledger": "ESG_MARINE", "amount": float(esg_share)})
        splits.append({"ledger": "CSR_TRAINING", "amount": float(csr_share)})

        # Tax & Service Charge
        splits.append({"ledger": "SOVEREIGN", "amount": quote["tax_amount"]})

        # Public Subsidy vs Commercial
        remaining = total - esg_csr_fee - Decimal(str(quote["tax_amount"]))

        if quote["is_public_subsidy"]:
            splits.append({"ledger": "PUBLIC_SUBSIDY", "amount": float(remaining)})
        else:
            # Commercial logic: Platform Fee (10%) + Supplier Payable
            platform_fee = (remaining * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            supplier_payable = remaining - platform_fee

            # Agent Commission (if applicable, e.g., 5% from supplier share)
            if booking_source in ["DMC", "TRAVEL_AGENT"]:
                commission = (supplier_payable * Decimal("0.05")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                supplier_payable -= commission
                splits.append({"ledger": "AGENT_COMMISSION", "amount": float(commission)})

            splits.append({"ledger": "PLATFORM_FEE", "amount": float(platform_fee)})
            splits.append({"ledger": "SUPPLIER_PAYABLE", "amount": float(supplier_payable)})

        return splits

    def release_payout(self, actor_ctx: dict, quote_id: str, orca_validated: bool, shadow_sealed: bool, apollo_synced: bool):
        """
        BLOCKS payout unless SHADOW + ORCA + APOLLO validation is complete.
        """
        if not (orca_validated and shadow_sealed and apollo_synced):
            raise PermissionError("PAYOUT BLOCKED: Requires ORCA + SHADOW + APOLLO validation")

        quote = self.quotes.get(quote_id)
        # Logic to trigger actual disbursement via FCE
        return {"status": "PAYOUT_RELEASED", "quote_id": quote_id}
