import pytest
from mnos.modules.prestige_social.quote_bridge.quote_models import QuoteRequest
from mnos.modules.prestige_social.quote_bridge.fce_quote_bridge import FCEQuoteBridge
from mnos.modules.prestige_social.quote_bridge.quote_status import QuoteStatus
from mnos.modules.prestige_social.sales_desk.sales_actions import generate_whatsapp_link

@pytest.fixture
def bridge():
    return FCEQuoteBridge()

@pytest.fixture
def sample_request():
    return {
        "request_id": "FCE-REQ-2026-000402",
        "lead_id": "PSC-LEAD-000402",
        "shadow_correlation_id": "sha256:lead_chain_hash",
        "source": {
            "platform": "instagram",
            "campaign_id": "SUNSET_VILLA_SERIES",
            "content_id": "REEL-0042",
            "user_handle": "@ahmed_travels"
        },
        "guest_profile": {
            "guest_name": "Ahmed",
            "market": "GCC",
            "country": "SA",
            "language": "en",
            "whatsapp_e164": "+966XXXXXXXXX",
            "pdpa_sales_consent": True
        },
        "trip_request": {
            "niche": "honeymoon",
            "travel_dates": {
                "check_in": "2026-07-10",
                "check_out": "2026-07-17",
                "nights": 7,
                "date_flexibility": "flexible"
            },
            "guests": {
                "adults": 2,
                "children": 0,
                "infants_under_2": 0,
                "total_green_taxable_guests": 2
            },
            "stay_preference": {
                "resort_id": "RITZ_CARLTON_MALDIVES",
                "resort_name": "The Ritz-Carlton Maldives, Fari Islands",
                "room_category": "overwater_villa",
                "meal_plan": "half_board",
                "special_occasion": "honeymoon"
            },
            "transfer": {
                "required": True,
                "mode": "speedboat",
                "arrival_airport": "MLE"
            },
            "budget_signal": {
                "original_currency": "USD",
                "original_amount": 10000,
                "usd_estimate": 10000,
                "note": "Budget signal"
            }
        },
        "pricing_rules": {
            "service_charge_rate": 0.10,
            "tgst_rate": 0.17,
            "prestige_margin_rule": "luxury_honeymoon_tier"
        },
        "quote_permissions": {
            "ai_can_send_to_guest": False,
            "human_approval_required": True
        }
    }

def test_quote_request_created_from_hot_lead(bridge, sample_request):
    req = QuoteRequest(**sample_request)
    response = bridge.process_quote_request(req, {"actor_type": "system", "actor_id": "TEST"})
    assert response.status == QuoteStatus.VERIFIED
    assert response.shadow.event == "FCE_QUOTE_VERIFIED"

def test_17_percent_tgst_enforced(bridge, sample_request):
    req = QuoteRequest(**sample_request)
    response = bridge.process_quote_request(req, {"actor_type": "system", "actor_id": "TEST"})
    assert response.price_breakdown.tgst_17_percent == pytest.approx(response.price_breakdown.taxable_subtotal * 0.17)
    assert response.compliance.tgst_rate_used == 0.17

def test_16_percent_tgst_blocked(bridge, sample_request):
    sample_request["pricing_rules"]["tgst_rate"] = 0.16
    with pytest.raises(ValueError, match="INVALID_TGST_RATE_2026"):
        QuoteRequest(**sample_request)

def test_usd_12_green_tax_for_resort(bridge, sample_request):
    req = QuoteRequest(**sample_request)
    response = bridge.process_quote_request(req, {"actor_type": "system", "actor_id": "TEST"})
    # 2 adults * 7 nights * 12 USD = 168
    assert response.price_breakdown.green_tax.amount == 168.0

def test_usd_6_green_tax_for_small_guesthouse(bridge, sample_request):
    sample_request["trip_request"]["stay_preference"]["resort_id"] = "FAMILY_GUESTHOUSE_SMALL"
    # Small guesthouse has 6 USD green tax
    req = QuoteRequest(**sample_request)
    response = bridge.process_quote_request(req, {"actor_type": "system", "actor_id": "TEST"})
    # 2 adults * 7 nights * 6 USD = 84
    assert response.price_breakdown.green_tax.amount == 84.0

def test_child_under_2_green_tax_exempt(bridge, sample_request):
    sample_request["trip_request"]["guests"]["infants_under_2"] = 1
    sample_request["trip_request"]["guests"]["total_green_taxable_guests"] = 2 # Still 2
    req = QuoteRequest(**sample_request)
    response = bridge.process_quote_request(req, {"actor_type": "system", "actor_id": "TEST"})
    assert response.price_breakdown.green_tax.taxable_guests == 2
    assert response.price_breakdown.green_tax.amount == 168.0

def test_ai_cannot_send_quote(bridge, sample_request):
    sample_request["quote_permissions"]["ai_can_send_to_guest"] = True
    with pytest.raises(ValueError, match="AI_QUOTE_SEND_FORBIDDEN"):
        QuoteRequest(**sample_request)

def test_whatsapp_open_logs_shadow_event():
    link = generate_whatsapp_link(
        whatsapp_e164="+966123456789",
        guest_name="Ahmed",
        agent_name="Sarah",
        nights=7,
        guest_count=2,
        resort_name="Ritz-Carlton",
        lead_id="PSC-001",
        quote_id="QUOTE-001",
        campaign_id="CAMP-001",
        human_agent_id="AGENT-001",
        shadow_correlation_id="HASH-001"
    )
    assert "wa.me" in link
    assert "Ahmed" in link
    assert "Ritz-Carlton" in link

def test_formula_correctness(bridge, sample_request):
    req = QuoteRequest(**sample_request)
    response = bridge.process_quote_request(req, {"actor_type": "system", "actor_id": "TEST"})

    pb = response.price_breakdown
    assert pb.selling_base == pb.base_contract_rate + pb.prestige_margin
    assert pb.service_charge_10_percent == pytest.approx(pb.selling_base * 0.10)
    assert pb.taxable_subtotal == pb.selling_base + pb.service_charge_10_percent
    assert pb.tgst_17_percent == pytest.approx(pb.taxable_subtotal * 0.17)
    assert pb.total_guest_payable == pytest.approx(pb.taxable_subtotal + pb.tgst_17_percent + pb.green_tax.amount + pb.transfer_fees)
