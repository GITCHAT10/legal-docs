import pytest
from datetime import datetime, timedelta, UTC
from uuid import uuid4
from mnos.modules.prestige.dashboards.command_center import CommandCenter
from mnos.modules.prestige.dashboards.status_models import ArrivalRecord, CommandStatus
from mnos.modules.prestige.outputs.brief_generator import BriefGenerator, BriefType
from mnos.modules.prestige.logistics.shadow_checklist import ShadowLogisticsChecklist, ChecklistItem
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.prestige.escalation.mac_eos_playbook import MacEosPlaybook

@pytest.fixture
def shadow():
    return ShadowLedger()

@pytest.fixture
def escalation(shadow):
    # Minimal mock or instance
    class MockCore:
        def __init__(self, s): self.shadow = s
        def execute_commerce_action(self, type, ctx, func, *args): return func(*args)
    return MacEosPlaybook(MockCore(shadow))

@pytest.fixture
def command_center(shadow, escalation):
    return CommandCenter(shadow, escalation)

@pytest.fixture
def checklist(shadow):
    return ShadowLogisticsChecklist(shadow)

@pytest.fixture
def brief_gen(command_center, checklist):
    return BriefGenerator(command_center, checklist)

def test_72h_arrivals_view(command_center):
    now = datetime.now(UTC)
    r1 = ArrivalRecord(booking_id="B1", guest_name="G1", arrival_time=now + timedelta(hours=10), privacy_level="P1")
    r2 = ArrivalRecord(booking_id="B2", guest_name="G2", arrival_time=now + timedelta(hours=80), privacy_level="P1")

    command_center.ingest_arrival(r1)
    command_center.ingest_arrival(r2)

    view = command_center.calculate_global_status(now)
    assert len(view) == 1
    assert view[0].booking_id == "B1"

def test_red_triggers_escalation(command_center, escalation):
    now = datetime.now(UTC)
    r = ArrivalRecord(booking_id="BRED", guest_name="G", arrival_time=now + timedelta(hours=5), privacy_level="P1", status=CommandStatus.RED)
    command_center.ingest_arrival(r)

    command_center.calculate_global_status(now)
    # Check if escalation opened
    assert "ESC-BRED" in escalation.escalations

def test_brief_blocks_if_red(brief_gen, command_center):
    command_center.ingest_arrival(ArrivalRecord(booking_id="BRED", guest_name="G", arrival_time=datetime.now(UTC), privacy_level="P1", status=CommandStatus.RED))

    with pytest.raises(ValueError, match="BLOCKED"):
        brief_gen.generate_brief("BRED", {}, BriefType.GUEST_FINAL, "P1")

def test_brief_privacy_safe_filtering(brief_gen, command_center, checklist):
    booking_id = "BP4"
    command_center.ingest_arrival(ArrivalRecord(booking_id=booking_id, guest_name="VIP", arrival_time=datetime.now(UTC), privacy_level="P4", logistics_seal=True))

    # Mock checklist seal
    checklist.checklists[booking_id] = {ChecklistItem.FINAL_24H_LOGISTICS_PROOF_SEALED: True}

    data = {
        "guest_name": "VIP",
        "logistics": [{"step": "boat", "vessel_gps": "1,1", "internal_staff_notes": "very vip"}]
    }

    brief = brief_gen.generate_brief(booking_id, data, BriefType.GUEST_FINAL, "P4")
    assert brief.guest_name == "Valued Guest" # models.py default or gen logic
    assert "vessel_gps" not in brief.transfer_logistics[0]
    assert "internal_staff_notes" not in brief.transfer_logistics[0]
