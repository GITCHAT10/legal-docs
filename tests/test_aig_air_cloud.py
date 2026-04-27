import pytest
from mnos.air_cloud.compute import SovereignComputeManager
from mnos.air_cloud.storage import SovereignStorageManager
from mnos.interfaces.api_fabric.gateway import SovereignGatewayOrchestrator
from mnos.interfaces.api_fabric.bridge import InterfaceBridge
from mnos.platform.mac_eos import MacEosBrain
from mnos.platform.orca import OrcaCommandCenter
from main import shadow_core, events_core, guard

@pytest.fixture
def cloud_stack():
    compute = SovereignComputeManager()
    storage = SovereignStorageManager()
    air_cloud = {"compute": compute, "storage": storage}

    gateway = SovereignGatewayOrchestrator(guard, shadow_core)
    bridge = InterfaceBridge(events_core, guard, shadow_core)
    api_fabric = {"gateway": gateway, "bridge": bridge}

    core = {"guard": guard, "shadow": shadow_core, "events": events_core}

    mac_eos = MacEosBrain(core, air_cloud, api_fabric)
    orca = OrcaCommandCenter(shadow_core, {}, {})

    return {
        "mac_eos": mac_eos,
        "orca": orca,
        "bridge": bridge,
        "compute": compute
    }

def test_e2e_signal_to_shadow_orchestration(cloud_stack):
    """
    Test Flow: API FABRIC Bridge -> MAC.EOS Orchestration -> SHADOW Audit.
    """
    actor_ctx = {"identity_id": "BOARD-MEMBER-01", "role": "admin"}

    # 1. Ingest Signal from Fabric Bridge (OTA Booking)
    signal_res = cloud_stack["bridge"].bridge_signal(
        source="Expedia-Connector",
        signal_type="ota_booking",
        payload={"booking_id": "OTA-882", "guest": "Ahmed"}
    )
    assert signal_res["status"] == "INGESTED"

    # 2. Trigger MAC.EOS Orchestration
    orch_res = cloud_stack["mac_eos"].orchestrate_workflow(
        workflow_type="GUEST_ONBOARDING",
        actor_ctx=actor_ctx,
        payload={"booking_id": "OTA-882", "data_sensitivity": "high"}
    )
    assert orch_res["status"] == "EXECUTING_IN_SOVEREIGN_ENVELOPE"
    # Sensitivity check: High sensitivity should use Sovereign Local compute
    assert orch_res["resource"]["tier"] == "NVIDIA_DGX_STATION"

    # 3. Verify SHADOW anchors
    assert any(b["event_type"] == "fabric.signal.ingested" for b in shadow_core.chain)
    assert any(b["event_type"] == "mac.execution.orchestrated" for b in shadow_core.chain)
    assert shadow_core.verify_integrity() is True

def test_full_sovereign_smoke_test(cloud_stack):
    """
    Final Smoke Test: booking → document seal → verified event → invoice → SHADOW
    """
    from mnos.core.fce.invoice import FceInvoiceEngine
    from mnos.core.doc.engine import SigDocEngine

    from main import fce_core
    invoice_engine = FceInvoiceEngine(fce_core, shadow_core, events_core)
    sigdoc = SigDocEngine(shadow_core)
    actor_ctx = {"identity_id": "STAFF-SMOKE", "role": "system"}

    # 1. Booking signal from Fabric
    cloud_stack["bridge"].bridge_signal(
        source="Booking-Portal",
        signal_type="ota_booking",
        payload={"id": "BK-99", "guest": "Zayan"}
    )

    # 2. Document Seal (Waybill/Folio)
    with guard.sovereign_context(actor=actor_ctx, trace_id="SMOKE-SIG"):
        seal_res = sigdoc.seal_document("STAFF-SMOKE", "FOLIO", {"guest": "Zayan", "amount": 2500})

    # 3. Verify Event (Reality Check)
    invoice_engine.register_delivery_event("BK-99", status="VERIFIED")

    # 4. Generate Invoice (NO EVENT -> NO INVOICE enforced)
    with guard.sovereign_context(actor=actor_ctx, trace_id="SMOKE-INV"):
        invoice = invoice_engine.generate_sovereign_invoice(
            actor_ctx,
            {"delivery_id": "BK-99", "total_base": 2500, "pax": 2, "nights": 1},
            document_hash=seal_res["seal"]
        )

    assert invoice["status"] == "SEALED"
    assert invoice["document_hash"] == seal_res["seal"]
    assert shadow_core.verify_integrity() is True
    print("🔥 SMOKE TEST PASSED: booking → seal → verified → invoice → SHADOW")

def test_orca_national_health_aggregation(cloud_stack):
    """
    Verify ORCA aggregated visibility.
    """
    report = cloud_stack["orca"].get_national_health_report()
    assert "infrastructure" in report
    assert "economic_activity" in report
    assert report["economic_activity"]["sync_integrity"] is True
    assert report["compliance"]["pdpa_data_residency"] == "SOVEREIGN_LOCAL_ENFORCED"

def test_compute_pii_gating(cloud_stack):
    """
    Verify compute resource allocation rules based on sensitivity.
    """
    # High sensitivity (PII) -> Local
    res_high = cloud_stack["compute"].allocate_ai_resource("high")
    assert res_high["tier"] == "NVIDIA_DGX_STATION"

    # Low sensitivity -> Global Burst
    res_low = cloud_stack["compute"].allocate_ai_resource("low")
    assert res_low["tier"] == "AWS_TRAINIUM"
