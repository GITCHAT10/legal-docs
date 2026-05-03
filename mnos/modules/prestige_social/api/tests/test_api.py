import pytest
from mnos.modules.prestige_social.quote_bridge.quote_models import QuoteRequest, QuoteStatus
from mnos.modules.prestige_social.quote_bridge.fce_quote_bridge import FCEQuoteBridge
from mnos.modules.prestige_social.api.social_lead_routes import router as lead_router, bridge as lead_bridge, lead_chains
from mnos.modules.prestige_social.api.quote_routes import router as quote_router, bridge as quote_bridge
from fastapi.testclient import TestClient
from fastapi import FastAPI

app = FastAPI()
app.include_router(lead_router)
app.include_router(quote_router)
client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_state():
    lead_bridge.quotes.clear()
    quote_bridge.quotes.clear()
    lead_chains.clear()

@pytest.fixture
def sample_request_data():
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

def test_full_integration_flow(sample_request_data):
    # 1. Request Quote
    response = client.post("/fce/quotes/request", json=sample_request_data)
    assert response.status_code == 200

    quote_id = list(quote_bridge.quotes.keys())[0]
    quote = quote_bridge.quotes[quote_id]
    assert quote.status == QuoteStatus.PENDING_HUMAN_VERIFICATION
    assert quote.approval.human_can_send is False

    # 2. Unverified quote cannot be sent
    response = client.post(f"/social/leads/PSC-LEAD-000402/send-quote?quote_id={quote_id}", json={"actor_type": "human", "actor_id": "SARAH"})
    assert response.status_code == 400
    assert response.json()["detail"] == "UNVERIFIED_QUOTE_SEND_BLOCKED"

    # 3. Verify Quote
    response = client.post(f"/fce/quotes/{quote_id}/verify")
    assert response.status_code == 200
    assert response.json()["status"] == "verified"
    assert quote_bridge.quotes[quote_id].status == QuoteStatus.VERIFIED
    assert quote_bridge.quotes[quote_id].approval.human_can_send is True

    # 4. Attach to Lead
    response = client.post(f"/social/leads/PSC-LEAD-000402/attach-quote?quote_id={quote_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "attached"

    # 5. Send Quote (Human Allowed)
    response = client.post(f"/social/leads/PSC-LEAD-000402/send-quote?quote_id={quote_id}", json={"actor_type": "human", "actor_id": "SARAH"})
    assert response.status_code == 200
    assert response.json()["status"] == "sent"

    # 6. Shadow Chain
    response = client.get("/social/leads/PSC-LEAD-000402/shadow-chain")
    assert response.status_code == 200
    chain = response.json()
    assert "QUOTE_ATTACHED_TO_LEAD" in chain
    assert "QUOTE_SENT_BY_HUMAN" in chain

def test_lead_to_quote_ownership_enforcement(sample_request_data):
    # Request Quote for Lead A
    client.post("/fce/quotes/request", json=sample_request_data)
    quote_id = list(quote_bridge.quotes.keys())[0]

    # Verify it
    client.post(f"/fce/quotes/{quote_id}/verify")

    # Attempt to send it for Lead B
    response = client.post(f"/social/leads/PSC-LEAD-DIFFERENT/send-quote?quote_id={quote_id}", json={"actor_type": "human", "actor_id": "SARAH"})
    assert response.status_code == 403
    assert "QUOTE_LEAD_MISMATCH" in response.json()["detail"]

def test_shadow_chain_integrity(sample_request_data):
    # 1. Request Quote
    client.post("/fce/quotes/request", json=sample_request_data)
    quote_id = list(quote_bridge.quotes.keys())[0]
    initial_hash = quote_bridge.quotes[quote_id].shadow.audit_hash
    correlation_id = quote_bridge.quotes[quote_id].shadow.parent_hash # lead_chain_hash

    # 2. Verify Quote
    client.post(f"/fce/quotes/{quote_id}/verify")
    verify_hash = quote_bridge.quotes[quote_id].shadow.audit_hash
    assert verify_hash != initial_hash

    # 3. Attach to Lead
    client.post(f"/social/leads/PSC-LEAD-000402/attach-quote?quote_id={quote_id}")
    attach_hash = lead_chains["PSC-LEAD-000402"][-1]["hash"]
    assert lead_chains["PSC-LEAD-000402"][-1]["parent_hash"] == verify_hash
    assert lead_chains["PSC-LEAD-000402"][-1]["correlation_id"] == correlation_id

    # 4. Mark Won
    response = client.post("/social/leads/PSC-LEAD-000402/mark-won", params={
        "quote_id": quote_id,
        "booking_ref": "BK-999",
        "revenue": 12014.90,
        "content_id": "REEL-0042",
        "campaign_id": "SUNSET",
        "actor_id": "SARAH"
    })
    assert response.status_code == 200
    won_event = lead_chains["PSC-LEAD-000402"][-1]
    assert won_event["parent_hash"] == attach_hash
    assert won_event["correlation_id"] == correlation_id
    assert won_event["hash"] != "..."
    assert won_event["parent_hash"] != "..."

def test_mark_won_lost_fail_closed_no_chain():
    # Attempt to mark won without any previous events for this lead
    response = client.post("/social/leads/LEAD-NONE/mark-won", params={
        "quote_id": "Q-1",
        "booking_ref": "BK-1",
        "revenue": 100,
        "content_id": "C-1",
        "campaign_id": "CAMP-1",
        "actor_id": "A-1"
    })
    assert response.status_code == 400
    assert "LEAD_CHAIN_NOT_FOUND" in response.json()["detail"]

def test_transfer_uncertainty_block(sample_request_data):
    # Set transfer mode to unknown
    sample_request_data["trip_request"]["transfer"]["mode"] = "unknown"
    client.post("/fce/quotes/request", json=sample_request_data)
    quote_id = list(quote_bridge.quotes.keys())[0]

    # Attempt to verify
    response = client.post(f"/fce/quotes/{quote_id}/verify")
    assert response.status_code == 400
    assert "TRANSFER_UNCERTAINTY_BLOCK" in response.json()["detail"]

def test_transfer_times_missing_block(sample_request_data):
    # Set transfer mode to seaplane and omit times
    sample_request_data["trip_request"]["transfer"]["mode"] = "seaplane"
    sample_request_data["trip_request"]["transfer"]["international_arrival_time"] = None
    client.post("/fce/quotes/request", json=sample_request_data)
    quote_id = list(quote_bridge.quotes.keys())[0]

    # Attempt to verify
    response = client.post(f"/fce/quotes/{quote_id}/verify")
    assert response.status_code == 400
    assert "TRANSFER_UNCERTAINTY_BLOCK" in response.json()["detail"]
