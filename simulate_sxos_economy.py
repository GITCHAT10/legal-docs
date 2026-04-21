from sqlalchemy.orm import Session
from skyfarm.database import SessionLocal, engine, Base
from sxos.finance.service import process_settlement
from sxos.tax.service import classify_and_calculate_tax
from sxos.esg.service import calculate_trip_esg
from sxos.logistics.service import optimize_route
from sxos.supply.service import fetch_and_compare_suppliers, calculate_landed_cost
from sxos.metrics.service import track_economic_metrics
from sxos.core.events import emit_sxos_event
import json
import os

# Ensure DB tables exist
Base.metadata.create_all(bind=engine)

def run_simulation():
    print("🚀 STARTING SXOS CLOSED ECONOMY SIMULATION...")
    db = SessionLocal()
    tenant_id = "resort_furaveri_001"

    # 1. Supply Discovery
    print("\n[1] Supply discovery for 'Industrial Generator'...")
    comparison = fetch_and_compare_suppliers("Industrial Generator")
    product = comparison["product"]
    print(f"Best Product: {product['name']} at ${product['price']}")

    # 2. Landed Cost Calculation
    print("\n[2] Calculating Landed Cost...")
    landed = calculate_landed_cost(product["price"], shipping_quote=150.0)
    print(f"Landed Cost Breakdown: {landed}")

    # 3. Tax Classification (MOATS)
    print("\n[3] Applying MOATS Tax logic...")
    items = [{"name": product["name"], "price": product["price"], "category": "cargo"}]
    tax_result = classify_and_calculate_tax(items)
    print(f"Tax Result: {tax_result}")

    # 4. Logistics Optimization
    print("\n[4] Optimizing Logistics Route...")
    route = optimize_route("Male Port", "Furaveri Resort", 500.0)
    print(f"Route Plan: {route}")

    # 5. ESG Tracking
    print("\n[5] Calculating Trip ESG Impact...")
    esg = calculate_trip_esg(150.0, 500.0, "vessel")
    print(f"ESG Report: {esg}")

    # 6. Settlement (FCE)
    print("\n[6] Processing Multi-Party Settlement...")
    settlement = process_settlement(db, tenant_id, "trans_abc_123", landed["total_landed"])
    print(f"Settlement Status: {settlement.status}")
    print(f"Distributions: {settlement.distributions}")

    # 7. Metrics
    print("\n[7] Generating Investor Metrics...")
    metrics = track_economic_metrics(landed["total_landed"], settlement.margin)
    print(f"System Metrics: {metrics}")

    # 8. Event Emission
    print("\n[8] Emitting full economy events to MNOS...")
    emit_sxos_event(db, tenant_id, "TRADE_EXECUTED", {"transaction_id": "trans_abc_123", "landed_cost": landed})
    emit_sxos_event(db, tenant_id, "TAX_APPLIED", tax_result)
    # Wrap list in dict to satisfy IntegrationPayload schema
    emit_sxos_event(db, tenant_id, "SETTLEMENT_COMPLETE", {"distributions": settlement.distributions})
    emit_sxos_event(db, tenant_id, "ESG_RECORDED", esg)

    db.close()
    print("\n✅ SIMULATION COMPLETE: SXOS Economic System is operational.")

if __name__ == "__main__":
    # Mock secrets for simulation
    os.environ["SKYFARM_INTEGRATION_SECRET"] = "sim_secret"
    os.environ["MNOS_INTEGRATION_SECRET"] = "sim_secret"
    run_simulation()
