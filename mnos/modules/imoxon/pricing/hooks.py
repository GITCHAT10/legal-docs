import structlog
import json
from .engine import PricingEngine, PricingRequest, PricingContext, PricingResponse

logger = structlog.get_logger()
engine = PricingEngine()

async def generate_quote_and_route(net_amount, product_type, context_dict, core=None):
    """
    Unified entry point for pricing that connects to SHADOW and EVENTS.
    """
    req = PricingRequest(
        net_amount=net_amount,
        product_type=product_type,
        context=PricingContext(**context_dict)
    )

    resp = engine.calculate(req)

    # 1. Log to Logger (Structured)
    logger.info("pricing_calculated",
        pricing_id=resp.pricing_id,
        trace_id=resp.trace_id,
        tax_type=resp.tax.tax_type,
        final_gross=str(resp.final_gross),
        margin_pct=resp.waterfall.margin_pct,
        compliance_hash=resp.compliance_hash
    )

    # 2. Integrate with MNOS Core (SHADOW + EVENTS)
    if core:
        # COMMIT TO SHADOW: Immutable Truth Point
        core.execute_commerce_action(
            "pricing.quote.generated",
            {"identity_id": "SYSTEM", "role": "admin", "device_id": "SYSTEM_VIRTUAL"},
            _internal_shadow_log,
            core, resp
        )

        # EMIT EVENT: Trigger downstream workflows (e.g., EXMAIL, Booking)
        core.events.publish("pricing.generated", resp.model_dump(mode="json"))

    return resp

def _internal_shadow_log(core, resp: PricingResponse):
    """Callback for SHADOW commit."""
    # We log the full breakdown for forensics
    payload = resp.model_dump(mode="json")
    # core.shadow is already handled by core.execute_commerce_action's wrapper logic in ImoxonCore
    return payload
