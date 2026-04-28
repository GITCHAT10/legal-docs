import structlog
from .engine import PricingEngine, PricingRequest, PricingContext
# Mocking these for now as they are not yet fully implemented or may have different paths
# from exmail.core.queue import AsyncEmailQueue
# from kpi.server import log_booking_event

logger = structlog.get_logger()
engine = PricingEngine()

async def generate_quote_and_route(net_amount, product_type, context_dict):
    req = PricingRequest(
        net_amount=net_amount,
        product_type=product_type,
        context=PricingContext(**context_dict)
    )

    resp = engine.calculate(req)

    # Log to SHADOW/KPI
    logger.info("pricing_calculated",
        pricing_id=resp.pricing_id,
        tax_type=resp.tax.tax_type,
        final_gross=str(resp.final_gross),
        margin_pct=resp.waterfall.margin_pct,
        compliance_hash=resp.compliance_hash
    )

    return resp
