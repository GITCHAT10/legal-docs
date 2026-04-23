import sys
import os
from datetime import datetime
import time

# Add the current directory to sys.path to import unified_suite
sys.path.append(os.getcwd())

from unified_suite.core.patente import NexGenPatenteVerifier
from unified_suite.tax_engine.calculator import MoatsTaxCalculator
import requests
import json
import hashlib
import hmac

def run_simulation():
    print("🚀 STARTING MALDIVES UNIFIED AIRPORT & PORT SUITE (XPORT) HARDENING SIMULATION")
    print("-" * 70)

    BASE_URL = "http://localhost:8003"

    # 1. SETUP NATIONAL ROOT SECRET
    os.environ["NEXGEN_SECRET"] = "NATIONAL_SECRET_2024"

    def get_patente(entity_id):
        # Correctly generate HMAC-based token
        sig = hmac.new(b"NATIONAL_SECRET_2024", entity_id.encode(), hashlib.sha256).hexdigest()
        return f"{entity_id}:{sig}"

    # 2. TEST: IDEMPOTENCY & ELEONE GATED EXECUTION
    print("\n[ELEONE] Testing Idempotent Flight Scheduling...")
    flight_id = "EK652"
    patente = get_patente(flight_id)

    headers = {
        "X-Entity-ID": flight_id,
        "X-NexGen-Patente": patente,
        "Content-Type": "application/json"
    }

    flight_data = {
        "flight_number": flight_id,
        "airline": "Emirates",
        "origin": "DXB",
        "destination": "MLE",
        "arrival_time": datetime.now().isoformat()
    }

    # First attempt
    resp1 = requests.post(f"{BASE_URL}/airports/flights", json=flight_data, headers=headers)
    print(f"Attempt 1: Status {resp1.status_code} - {resp1.json().get('flight_number') if resp1.status_code == 200 else resp1.text}")

    # Second attempt (Idempotency)
    resp2 = requests.post(f"{BASE_URL}/airports/flights", json=flight_data, headers=headers)
    print(f"Attempt 2: Status {resp2.status_code} - {resp2.json().get('flight_number') if resp2.status_code == 200 else resp2.text} (Should be identical)")

    # 3. TEST: AEGIS BINDING VIOLATION
    print("\n[AEGIS] Testing Token Binding Violation...")
    headers_stolen = headers.copy()
    headers_stolen["X-Entity-ID"] = "ATTACKER_ID"
    resp_stolen = requests.post(f"{BASE_URL}/airports/flights", json=flight_data, headers=headers_stolen)
    print(f"Stolen Token Attempt: Status {resp_stolen.status_code} - {resp_stolen.json().get('message')}")

    # 4. TEST: MOATS TAX LIABILITY LEDGER
    print("\n[MOATS] Verifying Tax Liability Ledger...")
    # Port Vessel
    vessel_id = "V_MSC_01"
    vessel_patente = get_patente(vessel_id)

    vessel_headers = {
        "X-Entity-ID": vessel_id,
        "X-NexGen-Patente": vessel_patente,
        "Content-Type": "application/json"
    }

    vessel_data = {
        "vessel_id": vessel_id,
        "name": "MSC MALDIVES",
        "origin": "SIN",
        "arrival_time": datetime.now().isoformat(),
        "containers": []
    }

    resp_vessel = requests.post(f"{BASE_URL}/seaports/vessels", json=vessel_data, headers=vessel_headers)
    print(f"Vessel Registration: Status {resp_vessel.status_code} - {resp_vessel.json().get('vessel_id')}")

    # 5. TEST: MALDIVES NATIVE SAFETY (Seaplane Night Ops)
    print("\n[SOVEREIGN SAFETY] Testing Seaplane Night Ops Restriction...")
    seaplane_id = "TMA_123"
    seaplane_patente = get_patente(seaplane_id)

    seaplane_headers = {
        "X-Entity-ID": seaplane_id,
        "X-NexGen-Patente": seaplane_patente,
        "Content-Type": "application/json"
    }

    # Midnight arrival
    seaplane_data = {
        "flight_number": seaplane_id,
        "airline": "TMA",
        "origin": "MLE",
        "destination": "KUREDU",
        "arrival_time": datetime(2024, 1, 1, 23, 0).isoformat()
    }

    resp_sea = requests.post(f"{BASE_URL}/airports/flights", json=seaplane_data, headers=seaplane_headers)
    print(f"Seaplane Night Landing: Status {resp_sea.status_code} - {resp_sea.json().get('detail')}")

    print("\n" + "-" * 70)
    print("✅ HARDENING SIMULATION COMPLETED")

if __name__ == "__main__":
    # Wait for services to be ready if running standalone
    run_simulation()
