import pytest
from uuid import uuid4
from decimal import Decimal
from mnos.modules.mios.engines.skygodown import SkyGodownEngine
from mnos.modules.mios.engines.freight import SkyFreightGDS, SkyParcelEngine
from mnos.modules.mios.engines.clearing import SkyClearingEngine
from mnos.modules.mios.engines.fce import MIOSFCEEngine
from mnos.modules.mios.engines.fx import MIOSFXEngine
from mnos.modules.mios.engines.handoff import MIOSAssetHandoffEngine
from mnos.modules.mios.schemas.models import CargoDWS
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.shared.execution_guard import ExecutionGuard

class MockShadow:
    def commit(self, event_type, actor_id, payload):
        return "hash"

@pytest.fixture
def actor_ctx():
    return {"identity_id": "actor-1", "role": "ADMIN"}

@pytest.fixture
def engines():
    # Use a real shadow ledger but mock auth for simplicity in these unit-style e2e tests
    # or just mock the shadow if we want to avoid ExecutionGuard issues.
    # Actually, ShadowLedger checks ExecutionGuard.is_authorized().
    # Let's set the system context to allow writes.
    from mnos.shared.execution_guard import _sovereign_context
    _sovereign_context.set({"token": "TEST-TOKEN", "actor": {"identity_id": "SYSTEM"}})

    shadow = ShadowLedger()
    return {
        "godown": SkyGodownEngine(shadow),
        "freight": SkyFreightGDS(shadow),
        "parcel": SkyParcelEngine(),
        "clearing": SkyClearingEngine(shadow),
        "fce": MIOSFCEEngine(shadow),
        "fx": MIOSFXEngine(shadow),
        "handoff": MIOSAssetHandoffEngine(shadow)
    }

def test_case_1_r40656_clean_path(engines, actor_ctx):
    godown = engines["godown"]
    fce = engines["fce"]
    clearing = engines["clearing"]
    handoff = engines["handoff"]

    shipment_id = uuid4()

    # 1. Receive Cargo
    # Case 1: Prefabricated container house, 493 packages, 9775 kg
    # We'll simulate this as a few large items for simplicity
    dws = CargoDWS(length_cm=Decimal("600"), width_cm=Decimal("240"), height_cm=Decimal("260"), actual_weight_kg=Decimal("9775"))
    cargo = godown.receive_cargo(actor_ctx, shipment_id, "Prefab House", dws)
    assert cargo.cargo_lane == "BLACK" # Project cargo due to weight/size

    # 2. Clearing Record
    record = clearing.create_record(actor_ctx, shipment_id, "ZH2411SE04/I", Decimal("11734"))
    record.invoice_verified = True
    record.hs_code = "94069000"
    record.hs_code_confirmed = True

    # 3. Customs & Port Charges (Seed values from Case 1)
    fce.add_line_item(actor_ctx, shipment_id, "CUSTOMS_CHARGES", "Duty/RVF/Proc", Decimal("1822.15"), True)
    fce.add_line_item(actor_ctx, shipment_id, "PORT_CHARGES", "MPL Total", Decimal("4790.88"), True)
    fce.add_line_item(actor_ctx, shipment_id, "TRANSPORT_CHARGES", "Inland Transport", Decimal("22996.66"), True)

    # 4. ORCA validation
    orca = clearing.validate_orca(shipment_id)
    assert orca["passed"] is True

    # 5. Service Charge
    sc = fce.calculate_sky_clearance_sc(shipment_id)
    # sc_base = 1822.15 + 4790.88 + 22996.66 = 29609.69
    # commission = 29609.69 * 0.03 = 888.29
    # total_sc = 750 + 888.29 = 1638.29
    assert sc == Decimal("1638.29")

    # 6. Landed Cost
    # Goods value = 11734 * 15.4180 = 180914.81
    fce.add_line_item(actor_ctx, shipment_id, "GOODS_VALUE", "Goods", Decimal("180914.81"), True)
    landed_cost = fce.get_landed_cost(shipment_id)
    # 180914.81 + 1822.15 + 4790.88 + 22996.66 = 210524.50
    assert landed_cost == Decimal("210524.50")

def test_case_2_zh_ro_water_01_blocked(engines, actor_ctx):
    clearing = engines["clearing"]
    shipment_id = uuid4()

    # Item: 500LPH RO Water Systems
    # Discrepancy found: Expected 1528, got 529 (invoice split issue)
    record = clearing.create_record(actor_ctx, shipment_id, "ZH_RO_WATER_01", Decimal("529"))
    record.invoice_verified = False # Blocked due to discrepancy
    record.hs_code = "94069000" # Wrong HS
    record.hs_code_confirmed = False # Blocked due to mismatch

    orca = clearing.validate_orca(shipment_id)
    assert orca["passed"] is False

    with pytest.raises(ValueError, match="ORCA validation failed"):
        clearing.submit_to_customs(actor_ctx, shipment_id, "DECL-001")

def test_sky_parcel_caps(engines):
    parcel = engines["parcel"]

    # Valid parcel
    dws_ok = CargoDWS(length_cm=Decimal("50"), width_cm=Decimal("40"), height_cm=Decimal("30"), actual_weight_kg=Decimal("10"))
    price = parcel.calculate_parcel_price("CN", dws_ok)
    # volumetric = 50*40*30 / 6000 = 10
    # chargeable = max(10, 10) = 10
    # subtotal = 8 + 10*3.5 = 43
    assert price == Decimal("43.00")

    # Oversized parcel (handled by SkyGodown lane logic)
    godown = engines["godown"]
    dws_big = CargoDWS(length_cm=Decimal("150"), width_cm=Decimal("40"), height_cm=Decimal("30"), actual_weight_kg=Decimal("10"))
    cargo = godown.receive_cargo({"identity_id": "actor-1"}, uuid4(), "Big box", dws_big)
    assert cargo.cargo_lane == "BLUE"
    assert cargo.parcel_eligible is False
