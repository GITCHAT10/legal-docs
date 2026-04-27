from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional
from enum import Enum
from mnos.modules.finance.fce import TaxType

class ProductType(str, Enum):
    ACCOMMODATION = "ACCOMMODATION"
    TRANSFER_SEA = "TRANSFER_SEA"
    TRANSFER_AIR = "TRANSFER_AIR"
    ACTIVITY = "ACTIVITY"
    FNB = "FNB"
    RETAIL = "RETAIL"
    SERVICE = "SERVICE"
    PACKAGE = "PACKAGE"
    FEE = "FEE"

class Channel(str, Enum):
    OTA = "OTA"           # 10% markup
    DIRECT = "DIRECT"     # Base price
    SOVEREIGN = "SOVEREIGN" # 5% discount

class PricingEngine:
    """
    Prestige Pricing Engine: Net rates + margin bands + FX + FCE validation.
    Implements the commission waterfall and enforces ROS/MNOS doctrine.
    """
    def __init__(self, fce):
        self.fce = fce
        self.fx_rates = {
            "USD": Decimal("15.42"),
            "EUR": Decimal("16.80"),
            "MVR": Decimal("1.00")
        }
        # Standard Margin Bands
        self.margin_bands = {
            ProductType.ACCOMMODATION: Decimal("0.15"),
            ProductType.TRANSFER_SEA: Decimal("0.10"),
            ProductType.TRANSFER_AIR: Decimal("0.08"),
            ProductType.ACTIVITY: Decimal("0.20"),
            ProductType.PACKAGE: Decimal("0.18"),
            "DEFAULT": Decimal("0.10")
        }
        self.commission_rates = {
            "B2B": Decimal("0.12"),
            "B2C": Decimal("0.00"),
            "PLATFORM": Decimal("0.02")
        }

    def calculate_quote(self,
                        net_amount: Decimal,
                        currency: str,
                        product_type: ProductType,
                        trace_id: str,
                        tax_type: TaxType = TaxType.TOURISM_STANDARD,
                        channel: Channel = Channel.DIRECT,
                        agent_type: str = "B2B",
                        allotment_override_pct: Optional[Decimal] = None) -> Dict[str, Any]:
        """
        Executes the full ROS Pricing Pipeline.
        """
        # 0. STRICT VALIDATION
        if net_amount is None or net_amount <= 0:
            raise ValueError(f"FAIL CLOSED: Valid net_amount required (Trace: {trace_id})")

        # 1. FX CONVERSION (Locked MVR base)
        fx_rate = self.fx_rates.get(currency.upper(), self.fx_rates["USD"])
        base_mvr = (net_amount * fx_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 2. CHANNEL MODIFIERS
        channel_modifier = Decimal("1.0")
        if channel == Channel.OTA:
            channel_modifier = Decimal("1.10")
        elif channel == Channel.SOVEREIGN:
            channel_modifier = Decimal("0.95")

        modified_base = (base_mvr * channel_modifier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 3. ALLOTMENT OVERRIDES
        applied_net = modified_base
        if allotment_override_pct:
            applied_net = (modified_base * (Decimal("1.0") + allotment_override_pct)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 4. MARGIN APPLICATION
        margin_pct = self.margin_bands.get(product_type, self.margin_bands["DEFAULT"])
        margin_amount = (applied_net * margin_pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        gross_before_tax = applied_net + margin_amount

        # 5. COMMISSION WATERFALL
        comm_rate = self.commission_rates.get(agent_type, self.commission_rates["B2B"])
        commission = (gross_before_tax * comm_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        platform_fee = (gross_before_tax * self.commission_rates["PLATFORM"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 6. FCE TAX ENGINE (Maldives Billing Rule: Base + 10% SC -> Tax)
        fce_result = self.fce.calculate_local_order(gross_before_tax, tax_type.value)

        # 7. ROS FULL BREAKDOWN
        price_breakdown = {
            "base_price": float(base_mvr),
            "cost_price": float(applied_net),
            "markup_pct": float(channel_modifier - 1),
            "margin_pct": float(margin_pct),
            "margin_amount": float(margin_amount),
            "commission_b2b": float(commission) if agent_type == "B2B" else 0,
            "commission_b2c": float(commission) if agent_type == "B2C" else 0,
            "platform_fee": float(platform_fee),
            "service_charge": fce_result["service_charge"],
            "tgst": fce_result["tax_amount"],
            "green_tax": fce_result["green_tax"],
            "discount": float(base_mvr - modified_base) if channel == Channel.SOVEREIGN else 0,
            "final_price": fce_result["total"],
            "currency": "MVR",
            "fx_rate_locked": float(fx_rate),
            "trace_id": trace_id
        }

        return {
            "status": "PRICED_LOCKED",
            "total_mvr": fce_result["total"],
            "breakdown": price_breakdown,
            "price_trace": price_breakdown # ROS compliance
        }

    def update_fx_rate(self, currency: str, rate: Decimal):
        self.fx_rates[currency.upper()] = rate
