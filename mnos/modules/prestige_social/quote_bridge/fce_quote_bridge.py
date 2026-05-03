from datetime import datetime, timedelta, UTC
import uuid
from .quote_models import QuoteRequest, QuoteResponse, PriceBreakdown, GreenTaxBreakdown, MVREquivalent, QuoteApproval, Compliance, ShadowMetadata, QuoteStatus
from .quote_rules import MOCK_RESORTS, SERVICE_CHARGE_RATE, TGST_RATE
from ..audit.shadow_quote_events import create_shadow_event

class FCEQuoteBridge:
    def __init__(self, shadow_core=None):
        self.shadow_core = shadow_core
        self.quotes = {}

    def process_quote_request(self, request: QuoteRequest, actor_ctx: dict) -> QuoteResponse:
        # 1. Validation Guards
        if request.pricing_rules.tgst_rate != 0.17:
            self._log_compliance_blocked(request, actor_ctx, "INVALID_TGST_RATE_2026")
            raise ValueError("INVALID_TGST_RATE_2026")

        if request.quote_permissions.ai_can_send_to_guest:
             self._log_compliance_blocked(request, actor_ctx, "AI_QUOTE_SEND_FORBIDDEN")
             raise ValueError("AI_QUOTE_SEND_FORBIDDEN")

        # 2. Get Mock Rate
        resort_id = request.trip_request.stay_preference.resort_id
        if resort_id not in MOCK_RESORTS:
             raise ValueError(f"Resort {resort_id} not found in mock contracts")

        contract = MOCK_RESORTS[resort_id]

        # 3. Calculate Pricing Waterfall
        base_contract_rate = contract["base_contract_rate"]
        # Prestige Margin (Mock logic)
        prestige_margin = 900.0 if request.pricing_rules.prestige_margin_rule == "luxury_honeymoon_tier" else 500.0

        selling_base = base_contract_rate + prestige_margin
        service_charge = selling_base * SERVICE_CHARGE_RATE
        taxable_subtotal = selling_base + service_charge
        tgst = taxable_subtotal * TGST_RATE

        # Green Tax calculation
        nights = request.trip_request.travel_dates.nights
        taxable_guests = request.trip_request.guests.total_green_taxable_guests
        green_tax_rate = contract["green_tax_rate"]
        green_tax_amount = green_tax_rate * taxable_guests * nights

        transfer_fees = contract["transfer_fee"]

        total_guest_payable = taxable_subtotal + tgst + green_tax_amount + transfer_fees

        # 4. Prepare Response
        quote_id = f"FCE-QUOTE-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"

        price_breakdown = PriceBreakdown(
            base_contract_rate=base_contract_rate,
            prestige_margin=prestige_margin,
            selling_base=selling_base,
            service_charge_10_percent=service_charge,
            taxable_subtotal=taxable_subtotal,
            tgst_17_percent=tgst,
            green_tax=GreenTaxBreakdown(
                rate_usd=green_tax_rate,
                taxable_guests=taxable_guests,
                nights_or_days=nights,
                amount=green_tax_amount
            ),
            transfer_fees=transfer_fees,
            total_guest_payable=total_guest_payable
        )

        mvr_equivalent = MVREquivalent(
            fx_rate=15.42,
            total_mvr=total_guest_payable * 15.42,
            fx_timestamp=datetime.now(UTC).isoformat()
        )

        # 5. Create SHADOW Event
        shadow_event = create_shadow_event(
            event_type="FCE_QUOTE_REQUESTED",
            lead_id=request.lead_id,
            actor_type="system",
            actor_id="FCE_BRIDGE",
            parent_hash=request.shadow_correlation_id,
            correlation_id=request.shadow_correlation_id,
            payload={"total_usd": total_guest_payable},
            quote_id=quote_id,
            request_id=request.request_id,
            content_id=request.source.content_id,
            campaign_id=request.source.campaign_id,
            source_platform=request.source.platform
        )

        response = QuoteResponse(
            request_id=request.request_id,
            lead_id=request.lead_id,
            quote_id=quote_id,
            status=QuoteStatus.PENDING_HUMAN_VERIFICATION,
            quote_valid_until=(datetime.now(UTC) + timedelta(days=1)).isoformat(),
            quote_summary={
                "resort_name": contract["name"],
                "room_category": request.trip_request.stay_preference.room_category,
                "meal_plan": request.trip_request.stay_preference.meal_plan,
                "nights": nights,
                "guests": request.trip_request.guests.dict(),
                "transfer": request.trip_request.transfer.dict()
            },
            price_breakdown=price_breakdown,
            mvr_equivalent=mvr_equivalent,
            approval=QuoteApproval(
                fce_verified=False,
                human_can_send=False,
                manager_approval_required=False,
                discount_allowed=False
            ),
            compliance=Compliance(),
            shadow=ShadowMetadata(
                event="FCE_QUOTE_REQUESTED",
                audit_hash=shadow_event["hash"],
                parent_hash=request.shadow_correlation_id
            )
        )

        self.quotes[quote_id] = response
        return response

    def _log_compliance_blocked(self, request, actor_ctx, reason):
        create_shadow_event(
            event_type="COMPLIANCE_BLOCKED",
            lead_id=request.lead_id,
            actor_type=actor_ctx.get("actor_type", "unknown"),
            actor_id=actor_ctx.get("actor_id", "unknown"),
            parent_hash=request.shadow_correlation_id,
            correlation_id=request.shadow_correlation_id,
            payload={"reason": reason},
            request_id=request.request_id
        )
