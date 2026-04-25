import pytest
from decimal import Decimal
from mnos.edge.node import EdgeNode
from mnos.core.events.durable_bus import event_bus
from mnos.modules.imoxon.ai_econ.engine import ai_econ
from mnos.modules.fce.clearing import fce_clearing
from mnos.modules.ut_simulation.waterfall import waterfall_sim
from mnos.modules.ut_simulation.oracle import dispatch_oracle

def test_edge_node_offline_fallback():
    node = EdgeNode("RESORT-01", "resort")
    node.is_online = False
    res = node.execute("provision_water", {"liters": 1000})
    assert res["status"] == "queued"
    assert len(node.queue) == 1

    node.is_online = True
    sync_res = node.sync()
    assert sync_res["synced"] == 1
    assert len(node.queue) == 0

def test_durable_bus_partitioning():
    event_bus.publish("ADDU-ATOLL", "SUPPLY_RECEIVED", {"item": "Fuel"})
    events = event_bus.replay("ADDU-ATOLL")
    assert len(events) >= 1
    assert events[0]["island_id"] == "ADDU-ATOLL"

def test_ai_econ_forecast():
    res = ai_econ.forecast_demand("BAA-ATOLL")
    assert res["forecast"] == "HIGH"
    assert res["confidence"] >= 0.9

def test_fce_clearing_split():
    res = fce_clearing.process_settlement(Decimal("1000.00"), ["Supplier-A", "Logistics-B"])
    assert res["tax"] == Decimal("170.00")
    assert res["party_share"] == Decimal("415.00")

def test_ut_waterfall_sim():
    res = waterfall_sim.calculate_waterfall(Decimal("10000.00"))
    assert res["tax"] == Decimal("1700.00")
    assert res["net"] == Decimal("10000.00") - Decimal("1700.00") - Decimal("500.00") - Decimal("5000.00") - Decimal("1500.00")

def test_dispatch_oracle_scoring():
    score = dispatch_oracle.calculate_consolidation_score(0.9, 0.8, 1.0, 0.9)
    assert score == 0.89
