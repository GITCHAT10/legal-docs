import pytest
from mnos.modules.prestige_social.quote_bridge.quote_models import QuoteRequest
from mnos.modules.prestige_social.quote_bridge.fce_quote_bridge import FCEQuoteBridge
from mnos.modules.prestige_social.quote_bridge.quote_status import QuoteStatus
from mnos.modules.prestige_social.api.social_lead_routes import router as lead_router, bridge as lead_bridge
from mnos.modules.prestige_social.api.quote_routes import router as quote_router, bridge as quote_bridge
from fastapi.testclient import TestClient
from fastapi import FastAPI

app = FastAPI()
app.include_router(lead_router)
app.include_router(quote_router)
client = TestClient(app)

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
    data = response.json()
    assert data["status"] == "pending"

    quote_id = quote_bridge.quotes[list(quote_bridge.quotes.keys())[0]].quote_id

    # 2. Verify Quote
    response = client.post(f"/fce/quotes/{quote_id}/verify")
    assert response.status_code == 200
    assert response.json()["status"] == "verified"

    # 3. Attach to Lead
    response = client.post(f"/social/leads/PSC-LEAD-000402/attach-quote?quote_id={quote_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "attached"

    # 4. Send Quote (AI Blocked)
    response = client.post(f"/social/leads/PSC-LEAD-000402/send-quote?quote_id={quote_id}", json={"actor_type": "ai", "actor_id": "ROBOT"})
    assert response.status_code == 403
    assert response.json()["detail"] == "AI_QUOTE_SEND_FORBIDDEN"

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

def test_human_cannot_send_unverified_quote(sample_request_data):
    # Request Quote
    client.post("/fce/quotes/request", json=sample_request_data)
    quote_id = list(quote_bridge.quotes.keys())[-1]
    quote_bridge.quotes[quote_id].status = "pending" # Force pending

    # Send Quote
    response = client.post(f"/social/leads/PSC-LEAD-000402/send-quote?quote_id={quote_id}", json={"actor_type": "human", "actor_id": "SARAH"})
    assert response.status_code == 400
    assert response.json()["detail"] == "UNVERIFIED_QUOTE_SEND_BLOCKED"

def test_booking_won(sample_request_data):
    response = client.post("/social/leads/PSC-LEAD-000402/mark-won", params={
        "quote_id": "FCE-QUOTE-001",
        "booking_ref": "BK-999",
        "revenue": 12014.90,
        "content_id": "REEL-0042",
        "campaign_id": "SUNSET",
        "actor_id": "SARAH"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "won"

def test_booking_lost():
    response = client.post("/social/leads/PSC-LEAD-000402/mark-lost", params={
        "loss_reason": "Too expensive",
        "actor_id": "SARAH"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "lost"
