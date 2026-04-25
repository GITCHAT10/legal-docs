import pytest
from decimal import Decimal
from mnos.modules.mercury_vine.services.intelligence import forecast_engine
from mnos.modules.mercury_vine.services.apollo_bridge import apollo_bridge
from mnos.modules.mercury_vine.services.execution import procurement_engine
from mnos.modules.fce.clearing import fce_clearing
from mnos.edge.node import EdgeNode

def test_national_os_procurement_cycle():
    # 1. Intelligence: Detect high stockout risk
    sku_risk = forecast_engine.predict_stockout("ONIONS", occupancy=100, inventory=50)
    assert sku_risk["risk_level"] == "HIGH"

    # 2. Decision: Apollo reroutes due to high weather risk
    route = apollo_bridge.decide_logistics_route("TIER_1", "HIGH", weather_risk=3.5)
    assert route == "AIR_BRIDGE"

    # 3. Execution: PR -> PO with Resilience Fee
    po = procurement_engine.create_purchase_order("RES-KAF-05", "SUP-MLE-01", Decimal("5000.00"))
    assert po["resilience_fee"] == Decimal("400.00") # 8% of 5000

    # 4. Clearing: Government Tax Split (17% TGST)
    settlement = fce_clearing.process_settlement(Decimal("5000.00"), ["Supplier"])
    assert settlement["tax"] == Decimal("850.00") # 17%

    # 5. Edge: Offline execution and sync
    node = EdgeNode("RES-KAF-05", "resort")
    node.is_online = False
    node.execute("GRN_VERIFY", {"po_id": po["po_id"]})
    assert len(node.queue) == 1

    node.is_online = True
    sync = node.sync()
    assert sync["synced"] == 1
