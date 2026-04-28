import uuid
import hashlib
import structlog
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Optional, Any
from datetime import datetime, timezone

logger = structlog.get_logger()

# ─────────────────────────────────────────────────────────────
# 1. STRICT I/O MODELS
# ─────────────────────────────────────────────────────────────
class PricingContext(BaseModel, extra="allow"):
    contract_id: Optional[str] = None
    segment: Optional[str] = "default"
    trigger: Optional[str] = "standard"
    allotment_pct: Optional[float] = 50.0
    currency: Optional[str] = "USD"
    tax_context: Optional[str] = None
    agent_id: Optional[str] = None

class PricingRequest(BaseModel):
    net_amount: Decimal = Field(gt=0)
    product_type: str
    context: PricingContext = PricingContext()

    @field_validator("product_type")
    @classmethod
    def validate_product(cls, v: str) -> str:
        allowed = {"accommodation", "transfer", "activity", "retail"}
        if v not in allowed:
            raise ValueError(f"Invalid product_type. Allowed: {allowed}")
        return v

class TaxBreakdown(BaseModel):
    service_charge: Decimal
    tgst: Decimal
    total_tax: Decimal
    tax_type: str

class MarginWaterfall(BaseModel):
    net_cost: Decimal
    margin_applied: Decimal
    margin_pct: float
    sell_price: Decimal
    agent_commission: Decimal
    platform_fee: Decimal
    net_profit: Decimal

class PricingResponse(BaseModel):
    pricing_id: str
    trace_id: str
    request: PricingRequest
    waterfall: MarginWaterfall
    tax: TaxBreakdown
    final_gross: Decimal
    currency: str
    timestamp: datetime
    compliance_hash: str

# ─────────────────────────────────────────────────────────────
# 2. CONFIG & GUARDRAILS
# ─────────────────────────────────────────────────────────────
MARGIN_BANDS = {
    "accommodation": Decimal("0.18"),
    "transfer": Decimal("0.12"),
    "activity": Decimal("0.22"),
    "retail": Decimal("0.10")
}

COMMISSION_RATES = {
    "agent": Decimal("0.10"),
    "platform": Decimal("0.05")
}

FX_RATES = {"USD": Decimal("1.00"), "EUR": Decimal("0.92"), "MVR": Decimal("15.42")}
FX_DEVIATION_LIMIT = Decimal("0.02")  # 2% max slippage

TAX_RULES = {
    "TOURISM": {"sc": Decimal("0.10"), "gst": Decimal("0.17")},
    "RETAIL": {"sc": Decimal("0.00"), "gst": Decimal("0.08")}
}

# ─────────────────────────────────────────────────────────────
# 3. CORE ENGINE
# ─────────────────────────────────────────────────────────────
class PricingEngine:
    def __init__(self, fce=None, fx_compliance=None):
        from mnos.modules.finance.fce import FCEEngine
        from mnos.modules.finance.fx_compliance import FXComplianceEngine
        self.fce = fce or FCEEngine()
        self.fx_compliance = fx_compliance or FXComplianceEngine()

    def resolve_tax_type(self, req: PricingRequest) -> str:
        if req.context.tax_context:
            return req.context.tax_context.upper()
        return "TOURISM" if req.product_type != "retail" else "RETAIL"

    def _scale_margin(self, base_pct: Decimal, context: PricingContext) -> Decimal:
        """Dynamic margin scaling based on allotment & trigger context"""
        pct = base_pct
        if context.allotment_pct is not None:
            if context.allotment_pct < 20:
                pct += Decimal("0.05")  # Urgency premium
            elif context.allotment_pct > 65:
                pct -= Decimal("0.03")  # Volume discount
        if context.trigger == "price_drop":
            pct -= Decimal("0.02")
        return max(pct, Decimal("0.05"))  # Floor 5%

    def _convert_currency(self, amount: Decimal, target: str) -> Decimal:
        rate = FX_RATES.get(target, Decimal("1.00"))
        return (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate(self, req: PricingRequest, user_nationality: str = "Foreign") -> PricingResponse:
        # 0. Generate Trace ID if missing
        trace_id = req.context.trigger or f"TR-{uuid.uuid4().hex[:8].upper()}"

        # 1. FX COMPLIANCE: Get legal rate
        locked_fx_rate = self.fx_compliance.get_compliant_fx_rate()

        # 2. MALDIVIAN USER RULE: Force MVR if local
        display_currency = req.context.currency or "USD"
        if user_nationality == "Maldivian":
            display_currency = "MVR"

        # 3. Tax Context
        tax_type = self.resolve_tax_type(req)

        # 4. Context-Aware Margin
        base_margin = MARGIN_BANDS.get(req.product_type, Decimal("0.10"))
        applied_margin = self._scale_margin(base_margin, req.context)
        margin_amount = (req.net_amount * applied_margin).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        sell_price = req.net_amount + margin_amount

        # 5. Commission Waterfall
        agent_comm = (sell_price * COMMISSION_RATES["agent"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        platform_fee = (sell_price * COMMISSION_RATES["platform"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        net_profit = sell_price - req.net_amount - agent_comm - platform_fee

        # 6. AUTHORITY CALL: Dual-Currency FCE Calculation
        fce_category = "TOURISM_STANDARD" if tax_type == "TOURISM" else "RETAIL"
        fce_result = self.fce.calculate_local_order(
            base_price=sell_price,
            category=fce_category,
            locked_fx_rate=locked_fx_rate,
            input_currency="USD"
        )

        final_gross_input = Decimal(str(fce_result["total_input_currency"]))
        final_gross_mvr = Decimal(str(fce_result["total_mvr"]))

        sc = Decimal(str(fce_result["service_charge"]))
        tgst = Decimal(str(fce_result["tax_amount"]))

        # 7. Final FX Conversion for display
        if display_currency == "MVR":
            final_gross_display = final_gross_mvr
        else:
            # Already in USD (input currency)
            final_gross_display = final_gross_input

        # 8. Build Objects
        waterfall = MarginWaterfall(
            net_cost=req.net_amount,
            margin_applied=margin_amount,
            margin_pct=float(applied_margin),
            sell_price=sell_price,
            agent_commission=agent_comm,
            platform_fee=platform_fee,
            net_profit=net_profit
        )
        tax = TaxBreakdown(
            service_charge=sc,
            tgst=tgst,
            total_tax=sc + tgst,
            tax_type=tax_type
        )

        # 9. Compliance Hash (Immutable Audit Trail)
        trace_data = f"{req.net_amount}|{applied_margin}|{agent_comm}|{platform_fee}|{sc}|{tgst}|{final_gross_input}"
        compliance_hash = hashlib.sha256(trace_data.encode()).hexdigest()[:16]

        return PricingResponse(
            pricing_id=str(uuid.uuid4()),
            trace_id=trace_id,
            request=req,
            waterfall=waterfall,
            tax=tax,
            final_gross=final_gross_display,
            currency=display_currency,
            timestamp=datetime.now(timezone.utc),
            compliance_hash=compliance_hash
        )

    def calculate_quote(self,
                        net_amount: Decimal,
                        currency: str,
                        product_type: str,
                        trace_id: str,
                        tax_type: Optional[str] = None,
                        channel: str = "DIRECT",
                        agent_type: str = "B2B",
                        allotment_override_pct: Optional[Decimal] = None) -> Dict[str, Any]:
        """
        Legacy compatibility method for calculate_quote.
        """
        # Map to new PricingRequest
        context = PricingContext(
            currency=currency,
            trigger=trace_id,
            allotment_pct=50.0 + (float(allotment_override_pct * 100) if allotment_override_pct else 0)
        )

        # Map product_type string to allowed values
        pt_map = {
            "ACCOMMODATION": "accommodation",
            "TRANSFER_SEA": "transfer",
            "TRANSFER_AIR": "transfer",
            "ACTIVITY": "activity",
            "PACKAGE": "accommodation",
            "RETAIL": "retail"
        }
        mapped_pt = pt_map.get(product_type.upper(), "accommodation")

        req = PricingRequest(
            net_amount=net_amount,
            product_type=mapped_pt,
            context=context
        )

        resp = self.calculate(req)

        # Convert response back to dictionary format expected by callers
        return {
            "status": "PRICED_LOCKED",
            "total_mvr": float(resp.final_gross) if currency == "MVR" else float(self._convert_currency(resp.final_gross, "MVR")),
            "breakdown": {
                "base_price": float(resp.request.net_amount),
                "cost_price": float(resp.waterfall.net_cost),
                "margin_pct": resp.waterfall.margin_pct,
                "margin_amount": float(resp.waterfall.margin_applied),
                "commission_b2b": float(resp.waterfall.agent_commission) if agent_type == "B2B" else 0,
                "platform_fee": float(resp.waterfall.platform_fee),
                "service_charge": float(resp.tax.service_charge),
                "tgst": float(resp.tax.tgst),
                "final_price": float(resp.final_gross),
                "trace_id": trace_id,
                "currency": currency
            },
            "price_trace": {
                "compliance_hash": resp.compliance_hash
            }
        }
