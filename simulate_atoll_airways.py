import requests
import json
import time
import os

BASE_URL = "http://localhost:8003"
# Reuse PATENTE_HASH logic from run_engine.sh
PATENTE_TOKEN = "dev_fallback_token"

def run_simulation():
    print("🚀 STARTING ATOLL AIRWAYS SEAPLANE SIMULATION (MARS EXTENSION)")
    print("-" * 65)

    headers = {
        "X-Entity-ID": "CAPT_MANTIS",
        "X-NexGen-Patente": PATENTE_TOKEN,
        "X-Request-ID": "SIM_ATOLL_001",
        "Content-Type": "application/json"
    }

    # 1. Resort Sync
    print("\n[RESORT SYNC] Checking Guest Readiness...")
    res = requests.get(f"{BASE_URL}/atoll_airways/resorts/RESORT_VILLA_01/guest-ready", headers=headers)
    print(f"Status: {res.json()}")

    # 2. Rotation Scheduling
    print("\n[ROTATION SCHEDULER] Generating Daily sectors for 8Q-TMA...")
    rotation_payload = {
        "aircraft_id": "8Q-TMA",
        "base": "VIA_LAGOON",
        "destinations": ["RESORT_A", "RESORT_B", "GAN"]
    }
    # Fix: generator endpoint takes aircraft_id in path
    res = requests.post(f"{BASE_URL}/atoll_airways/rotations/8Q-TMA?base=VIA_LAGOON&destinations=RESORT_A&destinations=RESORT_B&destinations=GAN", headers=headers)
    print(f"Generated {len(res.json())} sectors. Next available: {res.json()[0]['flight_id']}")

    # 3. Load Control & Dispatch
    print("\n[LOAD CONTROL & DISPATCH] Clearing Flight ROT_8Q-TMA_0_A for Takeoff...")
    dispatch_payload = {
        "manifest": {
            "flight_id": "ROT_8Q-TMA_0_A",
            "passenger_count": 14,
            "total_passenger_weight": 1100.0,
            "total_baggage_weight": 350.0
        },
        "zone": {
            "zone_id": "VIA_WATER_01",
            "location_name": "Velana Lagoon",
            "lanes": [
                {"lane_id": "LANE_09", "heading": 90},
                {"lane_id": "LANE_27", "heading": 270}
            ]
        }
    }

    res = requests.post(f"{BASE_URL}/atoll_airways/flights/ROT_8Q-TMA_0_A/dispatch", json=dispatch_payload, headers=headers)
    if res.status_code == 200:
        print(f"✅ DISPATCH SUCCESS: Lane {res.json()['lane']} assigned. Tax Applied: {res.json()['tax']['total_amount']} MVR")
    else:
        print(f"❌ DISPATCH FAILED: {res.text}")

    print("\n" + "-" * 65)
    print("✅ ATOLL AIRWAYS SIMULATION COMPLETE")

if __name__ == "__main__":
    # Wait a moment for server in run_engine.sh context, but assume it's running if called manually
    run_simulation()
