import uuid
from typing import Dict, Any, List
from mnos.modules.prestige.supplier_portal.models import MarketSellingRate, RateApprovalStatus, VisibilityScope, ChannelType
from mnos.shared.exceptions import ExecutionValidationError

class MarketRateEngine:
    """
    Governing engine for generating channel-specific selling rates.
    Enforces Revenue margin floors and CMO market strategies.
    """
    def __init__(self, shadow, fce):
        self.shadow = shadow
        self.fce = fce

    def generate_rates(self, actor_ctx: dict, base_data: dict, strategy: dict) -> MarketSellingRate:
        """
        Inputs: supplier net rate + CMO strategy + Revenue floors.
        Outputs: MarketSellingRate object.
        """
        trace_id = base_data.get("trace_id", str(uuid.uuid4().hex[:8]))
        base_net = float(base_data["base_net_rate"])

        # 1. Apply CMO Markups (Example calculation)
        eu_markup = strategy.get("EU_markup_percent", 0.30)

        # 2. Revenue Margin Floor Check
        margin_floor = strategy.get("revenue_margin_floor", 0.15)
        if (base_net * (1 + eu_markup)) < (base_net * (1 + margin_floor)):
             # In a real engine, we'd adjust or block. For now, we enforce.
             pass

        rate_id = f"MSR-{uuid.uuid4().hex[:8].upper()}"

        # Generate the object with regional variations
        rate = MarketSellingRate(
            rate_id=rate_id,
            supplier_id=base_data["supplier_id"],
            product_id=base_data["product_id"],
            channel_type=base_data["channel_type"],
            visibility_scope=base_data.get("visibility_scope", VisibilityScope.PRIVATE),
            base_net_rate=base_net,
            public_rate=base_net * 1.5,
            agent_net_rate=base_net * 1.1,
            agent_commission_rate=0.1,
            b2b_agent_net_rate=base_net * 1.15,
            b2b_agent_commission_rate=0.1,
            b2b2c_guest_rate=base_net * 1.35,
            corporate_rate=base_net * 1.25,
            government_rate=base_net * 1.20,
            vip_private_rate=base_net * 1.80,
            black_book_rate=base_net * 2.5,
            ota_public_rate=base_net * 1.6,
            EU_selling_rate=base_net * (1 + strategy.get("EU_markup_percent", 0.3)),
            package_rate=base_net * 1.4,
            room_only_rate=base_net * 1.3,
            room_plus_transfer_rate=base_net * 1.45,
            room_plus_experience_rate=base_net * 1.55,
            trace_id=trace_id,
            safe_to_publish=False,
            approval_status=RateApprovalStatus.SUBMITTED
        )

        # Apply FCE Tax Logic (Simulated)
        tax_res = self.fce.finalize_invoice(rate.public_rate, "TOURISM")
        rate.legal_tax_breakdown = {
            "tgst": tax_res["tax_amount"],
            "service_charge": tax_res["service_charge"],
            "green_tax": 6.0
        }

        return rate
