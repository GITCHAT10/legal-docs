import pytest
from decimal import Decimal
from mnos.modules.fce.valuation import valuation_engine
from mnos.modules.fce.tax_logic import tax_engine
from mnos.modules.esg.valuation_engine import esg_valuation
from mnos.modules.reporting.service import reporting_service
from mnos.shared.guard.service import guard
from mnos.core.aig_aegis.service import aig_aegis

@pytest.fixture
def valid_session():
    payload = {"device_id": "nexus-admin-01", "biometric_verified": True}
    sig = aig_aegis.sign_session(payload)
    payload["signature"] = sig
    return payload

@pytest.fixture
def valid_connection():
    return {
        "is_vpn": True,
        "tunnel_id": "tun-001",
        "encryption": "wireguard",
        "tunnel": "aig_tunnel",
        "source_ip": "10.0.0.1",
        "node_id": "CLOUD-01",
        "region": "MV"
    }

def test_dual_reporting_flow(valid_session, valid_connection):
    """
    Verify complete dual-reporting flow:
    Intent Capture -> Execution -> Shadow Seal -> Twin Reports
    """
    # 1. Capture Financial Intent
    amount_mvr = Decimal("1542.00")
    intent = valuation_engine.capture_intent(amount_mvr, "MV")
    assert intent["currency_local"] == "MVR"
    assert intent["amount_usd"] == Decimal("100.23") # 1542 * 0.065

    # 2. Execute via Hardened Guard
    def process_payment(p):
        return {"status": "PAID", "ref": "PAY-001"}

    res = guard.execute_sovereign_action(
        "payment.received",
        {"id": "PAY-001"},
        valid_session,
        process_payment,
        connection_context=valid_connection,
        financial_validation=True,
        financial_intent=intent,
        tenant="MIG-GENESIS")

    assert res["status"] == "PAID"

    # 3. Generate Twin Reports
    reports = reporting_service.generate_twin_reports(intent)
    assert reports["investor_report"]["amount_usd"] == intent["amount_usd"]
    assert reports["statutory_report"]["amount_local"] == amount_mvr

def test_regional_tax_logic():
    """Verify statutory tax calculation for multiple regions."""
    amount = Decimal("1000.00")

    mv_tax = tax_engine.calculate_tax(amount, "MV")
    assert mv_tax["tax"] == Decimal("170.00") # 17%

    th_tax = tax_engine.calculate_tax(amount, "TH")
    assert th_tax["tax"] == Decimal("70.00") # 7%

def test_esg_usd_normalization():
    """Verify ESG impact normalization to USD."""
    physical_co2 = Decimal("100.0")
    res = esg_valuation.normalize_impact(physical_co2)

    assert res["amount_usd"] == Decimal("2.50") # 100 * 0.025
    assert res["standard"] == "USD_PER_KG_CO2"

def test_th_regional_tunnel_warning(valid_session):
    """Verify regional tunnel binding logic for TH edge."""
    conn = {
        "is_vpn": True,
        "tunnel_id": "tun-th",
        "encryption": "wireguard",
        "tunnel": "aig_tunnel",
        "source_ip": "10.1.0.5",
        "node_id": "TH_EDGE_01",
        "region": "TH"
    }

    # Should pass without error but check logic path
    def mock_logic(p): return "OK"
    res = guard.execute_sovereign_action("test", {}, valid_session, mock_logic, connection_context=conn, tenant="MIG-GENESIS")
    assert res == "OK"
