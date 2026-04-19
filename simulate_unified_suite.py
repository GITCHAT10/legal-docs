import sys
import os
from datetime import datetime

# Add the current directory to sys.path to import unified_suite
sys.path.append(os.getcwd())

from unified_suite.core.patente import NexGenPatenteVerifier
from unified_suite.tax_engine.calculator import MoatsTaxCalculator
from unified_suite.airports.service import AirportService
from unified_suite.airports.models import Flight
from unified_suite.seaports.service import SeaPortService
from unified_suite.seaports.models import Vessel, Container
import requests
import json

def run_simulation():
    print("🚀 STARTING MALDIVES UNIFIED AIRPORT & PORT SUITE SIMULATION")
    print("-" * 60)

    # 1. NEXGEN PATENTE VERIFICATION
    print("\n[NEXGEN ASI PATENTE] Verifying Personnel...")
    captain_id = "CAPT_777"
    patente = NexGenPatenteVerifier.generate_patente(captain_id)

    # Set environment for standalone simulation auth
    import hashlib
    os.environ["PATENTE_HASH"] = hashlib.sha256(patente.encode()).hexdigest()

    is_valid = NexGenPatenteVerifier.authorize_access(patente, captain_id, "DOCKING_AREA")
    print(f"Captain {captain_id} Patente: {patente}")
    print(f"Authorization Status (DOCKING_AREA): {'✅ AUTHORIZED' if is_valid else '❌ DENIED'}")

    # 2. API INTEGRATION (Production Middleware)
    print("\n[PRODUCTION API] Testing Middleware Auth...")
    BASE_URL = "http://localhost:8003"
    headers = {
        "X-Entity-ID": captain_id,
        "X-NexGen-Patente": patente,
        "Content-Type": "application/json"
    }
    print("\n[AIRPORT SUITE] Scheduling Arrival at Velana International (VIA)...")
    airport = AirportService()
    flight = Flight(
        flight_number="EK652",
        airline="Emirates",
        origin="Dubai",
        destination="Male",
        arrival_time=datetime.now()
    )
    airport.schedule_flight(flight)
    gate = airport.assign_gate("EK652")
    print(f"Flight EK652 scheduled. Assigned Gate: {gate}")

    # 3. SEA PORT OPERATIONS (CONTAINER PORT)
    print("\n[SEA PORT SUITE] Vessel Arrival at Male Commercial Port...")
    seaport = SeaPortService()
    vessel = Vessel(
        vessel_id="V_MSC_01",
        name="MSC MALDIVES",
        origin="Colombo",
        arrival_time=datetime.now(),
        containers=[
            Container(container_id="CONT_A1", size=20, contents="Electronics", weight=15.5),
            Container(container_id="CONT_B2", size=40, contents="Textiles", weight=25.0)
        ]
    )
    seaport.register_vessel(vessel)
    berth = seaport.assign_berth("V_MSC_01")
    print(f"Vessel {vessel.name} docked at {berth}. Manifest contains {len(vessel.containers)} containers.")

    # 4. MOATS TAX LOGIC
    print("\n[MOATS TAX ENGINE] Calculating Port Dues & Airport Fees...")
    airport_fee_base = 1500.00
    port_fee_base = 5000.00

    airport_bill = MoatsTaxCalculator.calculate_bill(airport_fee_base)
    port_bill = MoatsTaxCalculator.calculate_bill(port_fee_base)

    print(f"Airport Bill (EK652): {airport_bill['total_amount']} {airport_bill['currency']} (TGST: {airport_bill['tgst']})")
    print(f"Port Bill (V_MSC_01): {port_bill['total_amount']} {port_bill['currency']} (TGST: {port_bill['tgst']})")
    print(f"Compliance Status: {airport_bill['compliance']}")

    print("\n" + "-" * 60)
    print("✅ SIMULATION COMPLETED SUCCESSFULLY")

if __name__ == "__main__":
    run_simulation()
