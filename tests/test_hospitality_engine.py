import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def admin_headers(create_security_headers):
    return create_security_headers(full_name="Admin", profile_type="admin")

@pytest.fixture
def airline_partner_headers(create_security_headers):
    return create_security_headers(full_name="Airline Staff", profile_type="airline_partner")

@pytest.fixture
def medical_headers(create_security_headers):
    return create_security_headers(full_name="Dr. Ahmed", profile_type="medical_worker")

@pytest.fixture
def user_headers(create_security_headers):
    return create_security_headers(full_name="Guest User", profile_type="user")

def test_airline_partner_discount(airline_partner_headers):
    # 1. Register Property
    prop_data = {"name": "Airport Hotel", "base_rate": 100.0}
    resp = client.post("/imoxon/hospitality/properties/register", json=prop_data, headers=airline_partner_headers)
    prop_id = resp.json()["id"]

    # 2. Book with industry discount (airline partner - 25%)
    booking_data = {"property_id": prop_id, "nights": 1}
    resp = client.post("/imoxon/hospitality/book", json=booking_data, headers=airline_partner_headers)
    assert resp.status_code == 200
    # Base 100 - 25% discount = 75.0 USD
    assert resp.json()["base_usd"] == 100.0
    assert resp.json()["discount_applied"] == 25.0

def test_medical_worker_discount(medical_headers):
    prop_data = {"name": "Health Stay", "base_rate": 200.0}
    resp = client.post("/imoxon/hospitality/properties/register", json=prop_data, headers=medical_headers)
    prop_id = resp.json()["id"]

    booking_data = {"property_id": prop_id, "nights": 1}
    resp = client.post("/imoxon/hospitality/book", json=booking_data, headers=medical_headers)
    assert resp.status_code == 200
    # Base 200 - 20% discount = 160.0 USD
    assert resp.json()["discount_applied"] == 40.0

def test_regular_user_no_discount(user_headers):
    prop_data = {"name": "Standard Lodge", "base_rate": 50.0}
    resp = client.post("/imoxon/hospitality/properties/register", json=prop_data, headers=user_headers)
    prop_id = resp.json()["id"]

    booking_data = {"property_id": prop_id, "nights": 1}
    resp = client.post("/imoxon/hospitality/book", json=booking_data, headers=user_headers)
    assert resp.status_code == 200
    assert resp.json()["discount_applied"] == 0.0

def test_maldives_taxes_applied(user_headers):
    prop_data = {"name": "Taxed Guesthouse", "base_rate": 50.0}
    resp = client.post("/imoxon/hospitality/properties/register", json=prop_data, headers=user_headers)
    prop_id = resp.json()["id"]

    booking_data = {"property_id": prop_id, "nights": 1}
    resp = client.post("/imoxon/hospitality/book", json=booking_data, headers=user_headers)
    assert resp.status_code == 200
    assert "pricing" in resp.json()
    assert "total" in resp.json()["pricing"]
