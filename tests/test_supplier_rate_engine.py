import pytest
from httpx import ASGITransport, AsyncClient
from main import app, identity_core, guard
from mnos.modules.imoxon.supplier.rate_models import ChannelType, VisibilityScope

@pytest.mark.anyio
async def test_supplier_rate_engine_full_workflow():
    """
    Scenario: Supplier intake -> Approval Flow -> Channel Gate Enforcement
    """
    SYSTEM_CTX = {"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}

    # 1. Setup Identities
    with guard.sovereign_context(SYSTEM_CTX):
        supplier_id = identity_core.create_profile({"full_name": "Supplier A", "profile_type": "supplier"})
        supplier_device = identity_core.bind_device(supplier_id, {"fingerprint": "supp_hw"})

        finance_id = identity_core.create_profile({"full_name": "Finance Reviewer", "profile_type": "finance_reviewer"})
        finance_device = identity_core.bind_device(finance_id, {"fingerprint": "fin_hw"})

        revenue_id = identity_core.create_profile({"full_name": "Revenue Reviewer", "profile_type": "revenue_reviewer"})
        revenue_device = identity_core.bind_device(revenue_id, {"fingerprint": "rev_hw"})

        cmo_id = identity_core.create_profile({"full_name": "CMO Reviewer", "profile_type": "cmo_reviewer"})
        cmo_device = identity_core.bind_device(cmo_id, {"fingerprint": "cmo_hw"})

        agent_id = identity_core.create_profile({"full_name": "B2B Agent", "profile_type": "agent_user"})
        agent_device = identity_core.bind_device(agent_id, {"fingerprint": "agent_hw"})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:

        supplier_headers = {
            "X-AEGIS-IDENTITY": supplier_id,
            "X-AEGIS-DEVICE": supplier_device,
            "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{supplier_id}"
        }

        # --- TEST 1: B2C rate requires public visibility ---
        b2c_payload = {
            "supplier_id": supplier_id,
            "product_id": "PROD-001",
            "channel_type": ChannelType.B2C_DIRECT,
            "visibility_scope": VisibilityScope.PRIVATE, # WRONG for B2C
            "base_net_rate": 1000.0
        }
        res = await ac.post("/imoxon/supplier-portal/rates/intake", json=b2c_payload, headers=supplier_headers)
        assert res.status_code == 200, res.text
        rate_id = res.json()["rate_id"]

        # Approval flow
        await ac.post(f"/imoxon/supplier-portal/rates/{rate_id}/approve?stage=FINANCE", headers={"X-AEGIS-IDENTITY": finance_id, "X-AEGIS-DEVICE": finance_device, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{finance_id}"})
        await ac.post(f"/imoxon/supplier-portal/rates/{rate_id}/approve?stage=REVENUE", headers={"X-AEGIS-IDENTITY": revenue_id, "X-AEGIS-DEVICE": revenue_device, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{revenue_id}"})

        # Final approval should fail due to B2C/PRIVATE mismatch
        res = await ac.post(f"/imoxon/supplier-portal/rates/{rate_id}/approve?stage=CMO", headers={"X-AEGIS-IDENTITY": cmo_id, "X-AEGIS-DEVICE": cmo_device, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{cmo_id}"})
        assert res.status_code == 400
        assert "B2C requires PUBLIC visibility" in res.text

        # --- TEST 2: B2B2C rate preserves margin floor ---
        b2b2c_payload = {
            "supplier_id": supplier_id,
            "product_id": "PROD-002",
            "channel_type": ChannelType.B2B2C_AGENT_TO_GUEST,
            "base_net_rate": 1000.0,
            "b2b_agent_net_rate": 1200.0,
            "b2b2c_guest_rate": 1100.0 # FAIL: Guest rate < Agent net
        }
        res = await ac.post("/imoxon/supplier-portal/rates/intake", json=b2b2c_payload, headers=supplier_headers)
        assert res.status_code == 200
        rate_id = res.json()["rate_id"]

        await ac.post(f"/imoxon/supplier-portal/rates/{rate_id}/approve?stage=FINANCE", headers={"X-AEGIS-IDENTITY": finance_id, "X-AEGIS-DEVICE": finance_device, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{finance_id}"})
        await ac.post(f"/imoxon/supplier-portal/rates/{rate_id}/approve?stage=REVENUE", headers={"X-AEGIS-IDENTITY": revenue_id, "X-AEGIS-DEVICE": revenue_device, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{revenue_id}"})
        res = await ac.post(f"/imoxon/supplier-portal/rates/{rate_id}/approve?stage=CMO", headers={"X-AEGIS-IDENTITY": cmo_id, "X-AEGIS-DEVICE": cmo_device, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{cmo_id}"})
        assert res.status_code == 400
        assert "guest rate must be higher than agent net rate" in res.text

        # --- TEST 3: B2G requires RESTRICTED or PRIVATE ---
        b2g_payload = {
            "supplier_id": supplier_id,
            "product_id": "PROD-003",
            "channel_type": ChannelType.B2G_GOVERNMENT,
            "visibility_scope": VisibilityScope.PUBLIC, # FAIL
            "base_net_rate": 1000.0
        }
        res = await ac.post("/imoxon/supplier-portal/rates/intake", json=b2g_payload, headers=supplier_headers)
        assert res.status_code == 200
        rate_id = res.json()["rate_id"]

        await ac.post(f"/imoxon/supplier-portal/rates/{rate_id}/approve?stage=FINANCE", headers={"X-AEGIS-IDENTITY": finance_id, "X-AEGIS-DEVICE": finance_device, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{finance_id}"})
        await ac.post(f"/imoxon/supplier-portal/rates/{rate_id}/approve?stage=REVENUE", headers={"X-AEGIS-IDENTITY": revenue_id, "X-AEGIS-DEVICE": revenue_device, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{revenue_id}"})
        res = await ac.post(f"/imoxon/supplier-portal/rates/{rate_id}/approve?stage=CMO", headers={"X-AEGIS-IDENTITY": cmo_id, "X-AEGIS-DEVICE": cmo_device, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{cmo_id}"})
        assert res.status_code == 400
        assert "B2G requires RESTRICTED or PRIVATE visibility" in res.text

        # --- TEST 4: Black Book requires P3/P4 Privacy ---
        bb_payload = {
            "supplier_id": supplier_id,
            "product_id": "PROD-004",
            "channel_type": ChannelType.BLACK_BOOK,
            "visibility_scope": VisibilityScope.PRIVATE, # FAIL: Needs P3/P4
            "base_net_rate": 1000.0
        }
        res = await ac.post("/imoxon/supplier-portal/rates/intake", json=bb_payload, headers=supplier_headers)
        assert res.status_code == 200
        rate_id = res.json()["rate_id"]

        await ac.post(f"/imoxon/supplier-portal/rates/{rate_id}/approve?stage=FINANCE", headers={"X-AEGIS-IDENTITY": finance_id, "X-AEGIS-DEVICE": finance_device, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{finance_id}"})
        await ac.post(f"/imoxon/supplier-portal/rates/{rate_id}/approve?stage=REVENUE", headers={"X-AEGIS-IDENTITY": revenue_id, "X-AEGIS-DEVICE": revenue_device, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{revenue_id}"})
        res = await ac.post(f"/imoxon/supplier-portal/rates/{rate_id}/approve?stage=CMO", headers={"X-AEGIS-IDENTITY": cmo_id, "X-AEGIS-DEVICE": cmo_device, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{cmo_id}"})
        assert res.status_code == 400
        assert "BLACK_BOOK requires P3/P4 Privacy scope" in res.text

        # --- TEST 5: Success Path & Black Book Visibility ---
        valid_bb_payload = {
            "supplier_id": supplier_id,
            "product_id": "PROD-005",
            "channel_type": ChannelType.BLACK_BOOK,
            "visibility_scope": VisibilityScope.P4_PRIVACY,
            "base_net_rate": 2000.0
        }
        res = await ac.post("/imoxon/supplier-portal/rates/intake", json=valid_bb_payload, headers=supplier_headers)
        assert res.status_code == 200
        rate_id = res.json()["rate_id"]

        await ac.post(f"/imoxon/supplier-portal/rates/{rate_id}/approve?stage=FINANCE", headers={"X-AEGIS-IDENTITY": finance_id, "X-AEGIS-DEVICE": finance_device, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{finance_id}"})
        await ac.post(f"/imoxon/supplier-portal/rates/{rate_id}/approve?stage=REVENUE", headers={"X-AEGIS-IDENTITY": revenue_id, "X-AEGIS-DEVICE": revenue_device, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{revenue_id}"})
        res = await ac.post(f"/imoxon/supplier-portal/rates/{rate_id}/approve?stage=CMO", headers={"X-AEGIS-IDENTITY": cmo_id, "X-AEGIS-DEVICE": cmo_device, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{cmo_id}"})
        assert res.status_code == 200
        assert res.json()["audit_seal"] is not None

        # Try to view as regular agent (FAIL)
        res = await ac.get(f"/imoxon/supplier-portal/rates/{rate_id}?channel=BLACK_BOOK", headers={"X-AEGIS-IDENTITY": agent_id, "X-AEGIS-DEVICE": agent_device, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{agent_id}"})
        assert res.status_code == 403
        assert "Black Book rates only visible to approved agents" in res.text

        # --- TEST 6: Unsealed rate never reaches any channel ---
        unapproved_payload = {
            "supplier_id": supplier_id,
            "product_id": "PROD-006",
            "channel_type": ChannelType.B2C_DIRECT,
            "visibility_scope": VisibilityScope.PUBLIC,
            "base_net_rate": 1000.0
        }
        res = await ac.post("/imoxon/supplier-portal/rates/intake", json=unapproved_payload, headers=supplier_headers)
        assert res.status_code == 200
        unapproved_rate_id = res.json()["rate_id"]

        # Try to view before approval (FAIL)
        res = await ac.get(f"/imoxon/supplier-portal/rates/{unapproved_rate_id}?channel=B2C_DIRECT", headers=supplier_headers)
        assert res.status_code == 400
        assert "Rate not found or not published" in res.text
