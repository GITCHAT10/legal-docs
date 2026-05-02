import pytest
from httpx import ASGITransport, AsyncClient
from main import app, identity_core, guard
from mnos.modules.prestige.supplier_portal.models import ChannelType, VisibilityScope

@pytest.mark.anyio
async def test_prestige_universal_commercial_readiness():
    """
    Scenario: Universal PMS -> Universal Supplier Portal -> Commercial Distribution
    """
    SYSTEM_CTX = {"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}

    with guard.sovereign_context(SYSTEM_CTX):
        # 1. Setup Identities
        supplier_id = identity_core.create_profile({"full_name": "Resort Supplier", "profile_type": "supplier"})
        supp_device = identity_core.bind_device(supplier_id, {"fingerprint": "supp_01"})
        identity_core.profiles[supplier_id]["verification_status"] = "verified"

        finance_id = identity_core.create_profile({"full_name": "Fin Controller", "profile_type": "finance_reviewer"})
        fin_device = identity_core.bind_device(finance_id, {"fingerprint": "fin_01"})
        identity_core.profiles[finance_id]["verification_status"] = "verified"

        revenue_id = identity_core.create_profile({"full_name": "Rev Manager", "profile_type": "revenue_reviewer"})
        rev_device = identity_core.bind_device(revenue_id, {"fingerprint": "rev_01"})
        identity_core.profiles[revenue_id]["verification_status"] = "verified"

        cmo_id = identity_core.create_profile({"full_name": "CMO", "profile_type": "cmo_reviewer"})
        cmo_device = identity_core.bind_device(cmo_id, {"fingerprint": "cmo_01"})
        identity_core.profiles[cmo_id]["verification_status"] = "verified"

        agent_id = identity_core.create_profile({"full_name": "Agent", "profile_type": "agent_user"})
        agent_device = identity_core.bind_device(agent_id, {"fingerprint": "agent_01"})

        bb_agent_id = identity_core.create_profile({"full_name": "Black Book Agent", "profile_type": "black_book_agent"})
        bb_device = identity_core.bind_device(bb_agent_id, {"fingerprint": "bb_01"})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:

        supp_headers = {"x-aegis-identity": supplier_id, "x-aegis-device": supp_device, "x-aegis-signature": f"VALID_SIG_FOR_{supplier_id}"}
        fin_headers = {"x-aegis-identity": finance_id, "x-aegis-device": fin_device, "x-aegis-signature": f"VALID_SIG_FOR_{finance_id}"}
        rev_headers = {"x-aegis-identity": revenue_id, "x-aegis-device": rev_device, "x-aegis-signature": f"VALID_SIG_FOR_{revenue_id}"}
        cmo_headers = {"x-aegis-identity": cmo_id, "x-aegis-device": cmo_device, "x-aegis-signature": f"VALID_SIG_FOR_{cmo_id}"}

        # --- TEST: PMS Adapter draft creation ---
        from mnos.modules.pms.adapters.placeholders import OperaAdapter
        adapter = OperaAdapter()
        raw_opera = {
            "res_id": "RES-123", "hotel_code": "HOTEL-A", "arrival": "2024-12-01",
            "departure": "2024-12-05", "room_type": "VILLA", "rate_amount": 1500.0
        }
        canonical = adapter.normalize(raw_opera)
        assert canonical.source_system == "OPERA"
        assert canonical.base_rate == 1500.0

        # --- TEST: Supplier Contract Upload ---
        res = await ac.post("/prestige/supplier-portal/contracts/upload", params={"supplier_id":"S1", "resort_name":"R1", "file_name":"f1"}, headers=supp_headers)
        assert res.status_code == 200

        # --- TEST: Rate Sheet Submission & Gate Enforcement ---
        rate_payload = {
            "supplier_id": supplier_id, "product_id": "P-001",
            "channel_type": ChannelType.BLACK_BOOK,
            "visibility_scope": VisibilityScope.P4_PRIVACY,
            "base_net_rate": 2000.0
        }
        res = await ac.post("/prestige/supplier-portal/rate-sheets/upload", json=rate_payload, headers=supp_headers)
        assert res.status_code == 200
        rate_id = res.json()["rate_id"]

        # Approval flow
        await ac.post(f"/prestige/supplier-portal/finance/review?rate_id={rate_id}", headers=fin_headers)
        await ac.post(f"/prestige/supplier-portal/revenue/review?rate_id={rate_id}", headers=rev_headers)
        res = await ac.post(f"/prestige/supplier-portal/cmo/market-strategy?rate_id={rate_id}", headers=cmo_headers)
        assert res.status_code == 200
        assert res.json()["approval_status"] == "ACTIVE_FOR_SALE"

        # --- TEST: Black Book Distribution Restriction ---
        res = await ac.get(f"/prestige/supplier-portal/rates/{rate_id}?channel=BLACK_BOOK", headers={"x-aegis-identity": agent_id, "x-aegis-device": agent_device, "x-aegis-signature": f"VALID_SIG_FOR_{agent_id}"})
        assert res.status_code == 403

        res = await ac.get(f"/prestige/supplier-portal/rates/{rate_id}?channel=BLACK_BOOK", headers={"x-aegis-identity": bb_agent_id, "x-aegis-device": bb_device, "x-aegis-signature": f"VALID_SIG_FOR_{bb_agent_id}"})
        assert res.status_code == 200
        assert res.json()["black_book_rate"] > 2000.0

        # --- TEST: Stop Sell immediate enforcement ---
        await ac.post(f"/prestige/supplier-portal/stop-sell?product_id=P-001", headers=supp_headers)
        res = await ac.get(f"/prestige/supplier-portal/rates/{rate_id}?channel=BLACK_BOOK", headers={"x-aegis-identity": bb_agent_id, "x-aegis-device": bb_device, "x-aegis-signature": f"VALID_SIG_FOR_{bb_agent_id}"})
        assert res.status_code == 400
        assert "STOP_SELL_IN_EFFECT" in res.text
