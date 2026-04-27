from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional
from enum import Enum

class TaxContext(str, Enum):
    TOURISM = "TOURISM"   # 17% TGST
    RETAIL = "RETAIL"     # 8% GST
    INTERNAL = "INTERNAL" # 0% Tax (or configured)

class Channel(str, Enum):
    OTA = "OTA"           # 10% markup
    DIRECT = "DIRECT"     # Base price
    SOVEREIGN = "SOVEREIGN" # 5% discount

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
                        tax_context: TaxContext = TaxContext.TOURISM,
                        channel: Channel = Channel.DIRECT,
                        agent_type: str = "AGENT_STANDARD",
                        allotment_override_pct: Optional[Decimal] = None) -> Dict[str, Any]:
        """
        Executes the full commission waterfall and FX conversion.
        Includes Allotment Overrides logic and Channel-based modifiers.
        """
        # 0. INPUT VALIDATION
        if net_amount <= 0:
            raise ValueError("FAIL CLOSED: Amount must be greater than zero")

        # 1. Convert to MVR (Base Currency)
        fx_rate = self.fx_rates.get(currency.upper(), self.fx_rates["USD"])
        net_mvr = (net_amount * fx_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 2. Apply Channel Rules (Moat/Revenue Optimization)
        channel_applied_net = net_mvr
        channel_modifier = Decimal("1.0")
        if channel == Channel.OTA:
            channel_modifier = Decimal("1.10")
        elif channel == Channel.SOVEREIGN:
            channel_modifier = Decimal("0.95")

        channel_applied_net = (net_mvr * channel_modifier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 3. Apply Allotment Override (if applicable)
        applied_net_mvr = channel_applied_net
        if allotment_override_pct:
            applied_net_mvr = (channel_applied_net * (Decimal("1.0") + allotment_override_pct)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 4. Apply Margin Band
        margin_pct = self.margin_bands.get(category.upper(), self.margin_bands["DEFAULT"])
        margin_amount = (applied_net_mvr * margin_pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        gross_amount = applied_net_mvr + margin_amount

        # 5. Calculate Waterfall Splits
        agent_comm_rate = self.commission_rates.get(agent_type, self.commission_rates["AGENT_STANDARD"])
        agent_commission = (gross_amount * agent_comm_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        platform_fee_rate = self.commission_rates["PLATFORM_FEE"]
        platform_fee = (gross_amount * platform_fee_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 6. FCE Validation (Apply Maldives Taxes: Base + SC + GST/TGST)
        # Enforces Maldives Billing Rule: Base + 10% SC = subtotal -> Tax on subtotal
        fce_result = self.fce.calculate_local_order(gross_amount, tax_context.value)

        # Audit Trace for SHADOW
        price_trace = {
            "net_orig": float(net_amount),
            "currency": currency.upper(),
            "fx_rate": float(fx_rate),
            "channel": channel.value,
            "channel_modifier": float(channel_modifier),
            "allotment_override": float(allotment_override_pct or 0),
            "margin_pct": float(margin_pct),
            "margin_amount": float(margin_amount),
            "gross_mvr": float(gross_amount),
            "agent_commission": float(agent_commission),
            "platform_fee": float(platform_fee),
            "tax_context": tax_context.value,
            "fce_breakdown": fce_result
        }

        return {
            "currency_orig": currency.upper(),
            "net_orig": float(net_amount),
            "fx_rate": float(fx_rate),
            "net_mvr": float(net_mvr),
            "gross_mvr": float(gross_amount),
            "agent_commission": float(agent_commission),
            "platform_fee": float(platform_fee),
            "fce_breakdown": fce_result,
            "total_mvr": fce_result["total"],
            "price_trace": price_trace,
            "status": "PRICED_LOCKED"
        }

    def update_fx_rate(self, currency: str, rate: Decimal):
        self.fx_rates[currency.upper()] = rate
