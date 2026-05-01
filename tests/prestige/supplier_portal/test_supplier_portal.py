import pytest
from mnos.modules.prestige.supplier_portal.contract_extraction import ContractExtractionEngine
from mnos.modules.prestige.supplier_portal.approval_workflow import ApprovalWorkflowOrchestrator
from mnos.modules.prestige.supplier_portal.market_rate_engine import MarketRateEngine
from mnos.modules.prestige.supplier_portal.models import SupplierAction, CMOMarketStrategyProfile

class MockShadow:
    def __init__(self):
        self.commits = []
    def commit(self, event_type, actor_id, payload):
        self.commits.append({"type": event_type, "actor": actor_id, "payload": payload})

class MockCore:
    def __init__(self):
        self.shadow = MockShadow()

@pytest.fixture
def core():
    return MockCore()

@pytest.fixture
def orchestrator(core):
    return ApprovalWorkflowOrchestrator(core, {})

def test_contract_extraction_creates_draft(core):
    engine = ContractExtractionEngine()
    result = engine.extract_from_pdf("Anantara_Kihavah_Contract.pdf")
    assert result.resort_name == "Anantara"
    assert result.status == "AI_EXTRACTED_DRAFT"
    assert len(result.room_rates) > 0

def test_approval_workflow_initiation(orchestrator):
    action = SupplierAction(
        action_id="ACT-001",
        supplier_id="SUP-001",
        resort_id="RES-001",
        action_type="RATE_SHEET_UPLOAD",
        submitted_by_actor_id="SUP-USER",
        submitted_at="2024-05-01",
        payload={},
        trace_id="TR-001"
    )
    task = orchestrator.initiate_approval(action)
    assert task.action_id == "ACT-001"
    assert "FINANCE" in task.required_approvals
    assert task.current_stage == "FINANCE"

def test_market_rate_generation_respects_markup(core):
    engine = MarketRateEngine()
    strategy = CMOMarketStrategyProfile(EU_markup_percent=10.0, agent_commission_percent=10.0)
    rates = engine.generate_market_rates(100.0, "BEACH_VILLA", strategy)

    eu_rate = next(r for r in rates if r.market_region == "EU")
    # 100 + 10% = 110 (Base Selling)
    # 110 + 11 (SC 10%) = 121
    # 121 + 20.57 (TGST 17%) = 141.57
    assert eu_rate.selling_rate == 141.57
    assert eu_rate.safe_to_publish == False

def test_stop_sell_immediate_activation(core, orchestrator):
    from mnos.modules.prestige.supplier_portal.supplier_actions import StopSellManager
    manager = StopSellManager(core, orchestrator)
    result = manager.submit_stop_sell({"identity_id": "SUP-1"}, {"resort_id": "RES-1", "room_category": "VILLA"})

    assert result["status"] == "success"
    assert any(c["type"] == "prestige.supplier.stop_sell_activated" for c in core.shadow.commits)

def test_full_approval_chain(orchestrator):
    action = SupplierAction(
        action_id="ACT-RATE",
        supplier_id="SUP-1",
        resort_id="RES-1",
        action_type="RATE_SHEET_UPLOAD",
        submitted_by_actor_id="SUP-USER",
        submitted_at="now",
        payload={},
        trace_id="TR-1"
    )
    task = orchestrator.initiate_approval(action)

    # 1. Finance
    orchestrator.record_decision(task.task_id, "FINANCE", "FIN-USER", "APPROVED", {})
    assert task.current_stage == "REVENUE"

    # 2. Revenue
    orchestrator.record_decision(task.task_id, "REVENUE", "REV-USER", "APPROVED", {})
    assert task.current_stage == "CMO"

    # 3. CMO
    orchestrator.record_decision(task.task_id, "CMO", "CMO-USER", "APPROVED", {})
    assert task.current_stage == "MAC_EOS"

    # 4. MAC_EOS
    orchestrator.record_decision(task.task_id, "MAC_EOS", "SYS", "APPROVED", {})
    assert task.current_stage == "FCE"

    # 5. FCE
    orchestrator.record_decision(task.task_id, "FCE", "SYS", "APPROVED", {})
    assert task.current_stage == "COMPLETED"
    assert orchestrator.actions["ACT-RATE"].status == "ACTIVE_FOR_SALE"
