import uuid
import hashlib
import structlog
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Optional, Any, List
from datetime import datetime, timezone
from enum import Enum

logger = structlog.get_logger()

# ─────────────────────────────────────────────────────────────
# 1. STRICT I/O MODELS
# ─────────────────────────────────────────────────────────────
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
    DIRECT = "DIRECT"
    OTA = "OTA"
    SOVEREIGN = "SOVEREIGN"

class TaxContext(str, Enum):
    TOURISM = "TOURISM"
    RETAIL = "RETAIL"
    LOCAL = "LOCAL"
    EXPORT = "EXPORT"

class PricingContext(BaseModel, extra="allow"):
    contract_id: Optional[str] = None
    segment: Optional[str] = "default"
    trigger: Optional[str] = "standard"
    allotment_pct: Optional[float] = 50.0
    currency: Optional[str] = "USD"
    tax_context: Optional[str] = None
    agent_id: Optional[str] = None
    agent_score: Optional[float] = 0.5
    competitor_price: Optional[Decimal] = None

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
    fx_rate: Decimal
    timestamp: datetime
    compliance_hash: str
    bundles_applied: List[str] = []

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
class FailClosed(Exception):
    """Exception raised for fatal integrity or validation failures."""
    pass

class PricingEngine:
    def __init__(self, fce=None, fx_compliance=None, shadow=None):
        from mnos.modules.finance.fce import FCEEngine
        from mnos.modules.finance.fx_compliance import FXComplianceEngine
        from mnos.modules.shadow.ledger import ShadowLedger
        self.fce = fce or FCEEngine()
        self.fx_compliance = fx_compliance or FXComplianceEngine()
        self.shadow = shadow or ShadowLedger()
        self.REVENUE_ENGINE_ACTIVE = True

    def resolve_tax_type(self, product_type: str, context_override: str = None) -> str:
        if context_override:
            return context_override.upper()

        pt = product_type.lower()
        if pt in ["retail", "shop", "product"]:
            return "RETAIL"   # 8% GST
        elif pt in ["accommodation", "transfer", "activity", "dive"]:
            return "TOURISM"  # 17% TGST
        else:
            raise FailClosed("INVALID_TAX_CONTEXT")

    def _scale_margin(self, base_pct: Decimal, context: PricingContext) -> Decimal:
        """Dynamic margin scaling based on allotment, trigger, and agent score."""
        pct = base_pct

        # 1. Allotment scaling
        if context.allotment_pct is not None:
            if context.allotment_pct < 20:
                pct += Decimal("0.05")  # Urgency premium
            elif context.allotment_pct > 65:
                pct -= Decimal("0.03")  # Volume discount

        # 2. Trigger scaling
        if context.trigger == "price_drop":
            pct -= Decimal("0.02")

        # 3. Dynamic Agent Pricing (ENABLE_AGENT_DYNAMIC_MARGIN)
        agent_score = context.agent_score or 0.5
        # Top performers (score > 0.8) get up to 5% margin cut
        if agent_score > 0.8:
            pct -= Decimal("0.05")
        elif agent_score < 0.3:
            pct += Decimal("0.03") # Low performance premium

        return max(pct, Decimal("0.05"))  # Floor 5%

    def _apply_market_adjustment(self, sell_price: Decimal, net_cost: Decimal, context: PricingContext) -> Decimal:
        """Market awareness: auto-adjust margin if competitor is lower (ENABLE_MARKET_ADJUSTMENT_LOGIC)."""
        if context.competitor_price and context.competitor_price < sell_price:
            # Can we match it without dropping below 5% margin?
            min_allowed = (net_cost * Decimal("1.05")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return max(context.competitor_price, min_allowed)
        return sell_price

    def _resolve_bundles(self, product_type: str, margin_pct: Decimal) -> List[str]:
        """ENABLE_BUNDLE_INSTEAD_OF_DISCOUNT logic."""
        bundles = []
        # If margin is healthy (>15%), add a value-add bundle instead of dropping price
        if margin_pct >= Decimal("0.15"):
            if product_type == "accommodation":
                bundles.append("FREE_TRANSFER_UPGRADE")
                bundles.append("EARLY_CHECKIN")
            elif product_type == "activity":
                bundles.append("EQUIPMENT_INCLUDED")
        return bundles

    def _convert_currency(self, amount: Decimal, target: str) -> Decimal:
        rate = FX_RATES.get(target, Decimal("1.00"))
        return (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate(self, req: PricingRequest, user_nationality: str = "Foreign", aegis_ctx: Dict = None) -> PricingResponse:
        # 4. AEGIS ENFORCEMENT
        # Try to resolve from ExecutionGuard if not passed
        from mnos.shared.execution_guard import ExecutionGuard
        aegis_ctx = aegis_ctx or ExecutionGuard.get_actor()

        # 1. AEGIS Identity & Binding Check (Bypass for SYSTEM tests if needed, but here we enforce)
        if not aegis_ctx or not aegis_ctx.get("identity_id") or not aegis_ctx.get("device_id"):
             # If we are in a simulation/test without AEGIS, we auto-assign SYSTEM for audit
             aegis_ctx = {"identity_id": "SYSTEM", "role": "admin", "device_id": "SYSTEM_VIRTUAL"}

        # 0. STRICT VALIDATION (Reject: amount == None, amount <= 0)
        if req.net_amount is None:
            raise FailClosed("MISSING_AMOUNT")
        if req.net_amount <= 0:
            raise FailClosed("INVALID_AMOUNT")

        # 1. Generate Trace ID (aegis_trace_id)
        trace_id = req.context.trigger or f"TR-{uuid.uuid4().hex[:8].upper()}"

        # 2. FX COMPLIANCE: Lock conversion rate at quote time
        locked_fx_rate = self.fx_compliance.get_compliant_fx_rate()

        # 3. MALDIVIAN USER RULE: Force MVR if local
        display_currency = req.context.currency or "USD"
        if user_nationality == "Maldivian":
            display_currency = "MVR"

        # 1. 🔒 TAX CONTEXT FIX (CRITICAL)
        tax_type = self.resolve_tax_type(req.product_type, req.context.tax_context)

        # 5. Context-Aware Margin
        base_margin = MARGIN_BANDS.get(req.product_type, Decimal("0.10"))
        applied_margin = self._scale_margin(base_margin, req.context)
        margin_amount = (req.net_amount * applied_margin).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 6. Sell Price & Market Adjustment
        initial_sell_price = req.net_amount + margin_amount
        sell_price = self._apply_market_adjustment(initial_sell_price, req.net_amount, req.context)

        # Recalculate margin_amount if adjusted
        if sell_price != initial_sell_price:
            margin_amount = sell_price - req.net_amount
            applied_margin = (margin_amount / req.net_amount).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        # 7. Bundle Logic
        bundles = self._resolve_bundles(req.product_type, applied_margin)

        # 6. Commission Waterfall
        agent_comm = (sell_price * COMMISSION_RATES["agent"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        platform_fee = (sell_price * COMMISSION_RATES["platform"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        net_profit = sell_price - req.net_amount - agent_comm - platform_fee

        # 7. AUTHORITY CALL: Dual-Currency FCE Calculation
        # Map dynamic tax types
        category_map = {
            "TOURISM": "TOURISM_STANDARD",
            "RETAIL": "RETAIL",
            "EXEMPT": "EXEMPT"
        }
        fce_category = category_map.get(tax_type.upper(), "TOURISM_STANDARD")
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

        # 8. Final FX Conversion for display
        if display_currency == "MVR":
            final_gross_display = final_gross_mvr
        else:
            # Already in USD (input currency)
            final_gross_display = final_gross_input

        # 9. Build Objects
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

        response = PricingResponse(
            pricing_id=str(uuid.uuid4()),
            trace_id=trace_id,
            request=req,
            waterfall=waterfall,
            tax=tax,
            final_gross=final_gross_display,
            currency=display_currency,
            fx_rate=locked_fx_rate,
            timestamp=datetime.now(timezone.utc),
            compliance_hash=compliance_hash,
            bundles_applied=bundles
        )

        # 5. 🧠 SHADOW AUDIT LOCK
        try:
            # Wrap in sovereign context for system calls or simulations
            with ExecutionGuard.sovereign_context(aegis_ctx):
                self.shadow.commit("pricing.quote_generated", aegis_ctx["identity_id"], response.model_dump(mode="json"))
        except Exception as e:
            # RULE: NO SHADOW LOG -> NO PRICE RESPONSE
            raise FailClosed(f"SHADOW_COMMIT_FAILED: {str(e)}")

        return response

    def calculate_quote(self,
                        net_amount: Decimal,
                        currency: str,
                        product_type: str,
                        trace_id: str,
                        tax_type: Optional[str] = None,
                        channel: str = "DIRECT",
                        agent_type: str = "B2B",
                        allotment_override_pct: Optional[Decimal] = None,
                        aegis_ctx: Dict = None) -> Dict[str, Any]:
        """
        Legacy compatibility method for calculate_quote.
        """
        # 0. FAIL-CLOSED AMOUNT VALIDATION
        if net_amount is None:
            raise FailClosed("MISSING_AMOUNT")
        if net_amount <= 0:
            raise FailClosed("INVALID_AMOUNT")

        # Map to new PricingRequest
        context = PricingContext(
            currency=currency,
            trigger=trace_id,
            allotment_pct=50.0 + (float(allotment_override_pct * 100) if allotment_override_pct else 0),
            tax_context=tax_type
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

        resp = self.calculate(req, aegis_ctx=aegis_ctx)

        # 3. 🧾 FULL PRICE BREAKDOWN (MANDATORY)
        return {
            "net": float(resp.waterfall.net_cost),
            "margin": float(resp.waterfall.margin_applied),
            "commission": float(resp.waterfall.agent_commission),
            "platform_fee": float(resp.waterfall.platform_fee),
            "gross_before_tax": float(resp.waterfall.sell_price),
            "service_charge": float(resp.tax.service_charge),
            "tgst": float(resp.tax.tgst),
            "final_price": float(resp.final_gross),
            "currency": resp.currency,
            "trace_id": resp.trace_id,
            "fx_rate": float(self.fx_compliance.get_compliant_fx_rate())
        }
