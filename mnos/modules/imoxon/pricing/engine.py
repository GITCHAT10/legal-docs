from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional

class PricingEngine:
    """
    Prestige Pricing Engine: Net rates + margin bands + FX + FCE validation.
    Implements the commission waterfall: net -> margin -> fee -> commission -> platform.
    """
    def __init__(self, fce):
        self.fce = fce
        # Default FX Rates (MVR base)
        self.fx_rates = {
            "USD": Decimal("15.42"),
            "EUR": Decimal("16.80"),
            "MVR": Decimal("1.00")
        }
        # Margin Bands based on product category
        self.margin_bands = {
            "ACCOMMODATION": Decimal("0.15"), # 15%
            "TRANSFER": Decimal("0.10"),      # 10%
            "EXCURSION": Decimal("0.20"),     # 20%
            "PACKAGE": Decimal("0.18"),       # 18%
            "DEFAULT": Decimal("0.10")
        }
        # Platform/Agent Fees
        self.commission_rates = {
            "AGENT_STANDARD": Decimal("0.10"),
            "PLATFORM_FEE": Decimal("0.02")
        }

    def calculate_quote(self, net_amount: Decimal, currency: str, category: str,
                        agent_type: str = "AGENT_STANDARD",
                        allotment_override_pct: Optional[Decimal] = None) -> Dict[str, Any]:
        """
        Executes the full commission waterfall and FX conversion.
        Includes Allotment Overrides logic for dynamic pricing adjustments.
        """
        # 1. Convert to MVR (Base Currency)
        fx_rate = self.fx_rates.get(currency.upper(), self.fx_rates["USD"])
        net_mvr = (net_amount * fx_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 2. Apply Allotment Override (if applicable)
        # Dynamic adjustment based on contract volume / stop-sale proximity
        applied_net_mvr = net_mvr
        if allotment_override_pct:
            applied_net_mvr = (net_mvr * (Decimal("1.0") + allotment_override_pct)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 3. Apply Margin Band
        margin_pct = self.margin_bands.get(category.upper(), self.margin_bands["DEFAULT"])
        margin_amount = (applied_net_mvr * margin_pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        gross_amount = applied_net_mvr + margin_amount

        # 4. Calculate Waterfall Splits
        # Agent commission is calculated from the margin to protect net profitability
        agent_comm_rate = self.commission_rates.get(agent_type, self.commission_rates["AGENT_STANDARD"])
        agent_commission = (gross_amount * agent_comm_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        platform_fee_rate = self.commission_rates["PLATFORM_FEE"]
        platform_fee = (gross_amount * platform_fee_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 5. FCE Validation (Apply Maldives Taxes: Base + SC + GST)
        # We treat 'gross_amount' as the base price for FCE calculation
        fce_result = self.fce.calculate_local_order(gross_amount, "TOURISM")

        return {
            "currency_orig": currency.upper(),
            "net_orig": float(net_amount),
            "fx_rate": float(fx_rate),
            "net_mvr": float(net_mvr),
            "margin_pct": float(margin_pct),
            "margin_amount": float(margin_amount),
            "gross_mvr": float(gross_amount),
            "agent_commission": float(agent_commission),
            "platform_fee": float(platform_fee),
            "fce_breakdown": fce_result,
            "total_mvr": fce_result["total"],
            "status": "PRICED_LOCKED"
        }

    def update_fx_rate(self, currency: str, rate: Decimal):
        self.fx_rates[currency.upper()] = rate
