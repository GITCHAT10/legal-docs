import pytest
from httpx import ASGITransport, AsyncClient
from main import app, identity_core, guard, shadow_core, prestige_portal
from mnos.modules.prestige.supplier_portal.models import ChannelType, VisibilityScope
import uuid

@pytest.mark.anyio
async def test_full_commercial_readiness_suite():
    SYSTEM_CTX = {"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}

    with guard.sovereign_context(SYSTEM_CTX):
        supplier_id = identity_core.create_profile({"full_name": "Universal Supplier", "profile_type": "supplier"})
        supp_device = identity_core.bind_device(supplier_id, {"fingerprint": "supp_99"})
        identity_core.profiles[supplier_id]["verification_status"] = "verified"

        finance_id = identity_core.create_profile({"full_name": "Finance", "profile_type": "finance_reviewer"})
        fin_device = identity_core.bind_device(finance_id, {"fingerprint": "fin_99"})
        identity_core.profiles[finance_id]["verification_status"] = "verified"

        revenue_id = identity_core.create_profile({"full_name": "Revenue", "profile_type": "revenue_reviewer"})
        rev_device = identity_core.bind_device(revenue_id, {"fingerprint": "rev_99"})
        identity_core.profiles[revenue_id]["verification_status"] = "verified"

        cmo_id = identity_core.create_profile({"full_name": "CMO", "profile_type": "cmo_reviewer"})
        cmo_device = identity_core.bind_device(cmo_id, {"fingerprint": "cmo_99"})
        identity_core.profiles[cmo_id]["verification_status"] = "verified"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:

        supp_headers = {
            "X-AEGIS-IDENTITY": supplier_id, "X-AEGIS-DEVICE": supp_device,
            "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{supplier_id}"
        }
        fin_headers = {
            "X-AEGIS-IDENTITY": finance_id, "X-AEGIS-DEVICE": fin_device,
            "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{finance_id}"
        }
        rev_headers = {
            "X-AEGIS-IDENTITY": revenue_id, "X-AEGIS-DEVICE": rev_device,
            "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{revenue_id}"
        }
        cmo_headers = {
            "X-AEGIS-IDENTITY": cmo_id, "X-AEGIS-DEVICE": cmo_device,
            "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{cmo_id}"
        }

        # --- [PMS CONNECTOR] ---
        from mnos.modules.pms.adapters.placeholders import OperaAdapter
        adapter = OperaAdapter()
        raw_opera = {"res_id": "OP-1", "hotel_code": "HOTEL-X", "arrival": "2024-12-01", "departure": "2024-12-05", "room_type": "VILLA", "rate_amount": 1000.0}
        canonical = adapter.normalize(raw_opera)
        assert canonical.source_system == "OPERA"

        # --- [CONTRACT UPLOAD] ---
        res = await ac.post("/prestige/supplier-portal/contracts/upload", params={"supplier_id":"S1", "resort_name":"R1", "file_name":"f1"}, headers=supp_headers)
        if res.status_code != 200:
             print(f"DEBUG BODY: {res.text}")
        assert res.status_code == 200

        # --- [RATE SHEET SUBMISSION] ---
        rate_payload = {
            "supplier_id": supplier_id, "product_id": "P-VILLA-01",
            "channel_type": ChannelType.B2C_DIRECT,
            "visibility_scope": VisibilityScope.PUBLIC,
            "base_net_rate": 1500.0
        }
        res = await ac.post("/prestige/supplier-portal/rate-sheets/upload", json=rate_payload, headers=supp_headers)
        assert res.status_code == 200
        rate_id = res.json()["rate_id"]

        # --- [APPROVAL FLOW] ---
        res = await ac.post(f"/prestige/supplier-portal/finance/review?rate_id={rate_id}", headers=fin_headers)
        assert res.status_code == 200
        res = await ac.post(f"/prestige/supplier-portal/revenue/review?rate_id={rate_id}", headers=rev_headers)
        assert res.status_code == 200
        res = await ac.post(f"/prestige/supplier-portal/cmo/market-strategy?rate_id={rate_id}", headers=cmo_headers)
        assert res.status_code == 200

        # --- [CHANNEL GATES] ---
        res = await ac.get(f"/prestige/supplier-portal/rates/{rate_id}?channel=B2C_DIRECT", headers=supp_headers)
        assert res.status_code == 200

        # --- [STOP SELL] ---
        await ac.post(f"/prestige/supplier-portal/stop-sell?product_id=P-VILLA-01", headers=supp_headers)
        res = await ac.get(f"/prestige/supplier-portal/rates/{rate_id}?channel=B2C_DIRECT", headers=supp_headers)
        assert res.status_code == 400
        assert "STOP_SELL_IN_EFFECT" in res.text
