from ..quote_bridge.quote_models import QuoteResponse
from ..quote_bridge.quote_status import QuoteStatus

def build_quote_panel(quote: QuoteResponse):
    return {
        "status": quote.status,
        "quote_id": quote.quote_id,
        "quote_valid_until": quote.quote_valid_until,
        "total_guest_payable": quote.price_breakdown.total_guest_payable,
        "currency": quote.currency,
        "mvr_equivalent": quote.mvr_equivalent.total_mvr,
        "base_contract_rate": quote.price_breakdown.base_contract_rate,
        "prestige_margin": quote.price_breakdown.prestige_margin,
        "service_charge_10_percent": quote.price_breakdown.service_charge_10_percent,
        "tgst_17_percent": quote.price_breakdown.tgst_17_percent,
        "green_tax": quote.price_breakdown.green_tax.amount,
        "transfer_fee": quote.price_breakdown.transfer_fees,
        "compliance_status": "VERIFIED" if quote.approval.fce_verified else "UNVERIFIED",
        "human_can_send": quote.approval.human_can_send
    }
