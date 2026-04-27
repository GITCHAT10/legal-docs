import json
import time

def show_dashboard():
    # Mock authentication headers (System/Admin)
    headers = {
        "X-AEGIS-SESSION": "MOCK-SESSION-SALA-ADMIN"
    }

    from fastapi.testclient import TestClient
    from main import app, identity_gateway, guard

    client = TestClient(app)

    # Setup session
    SYSTEM_CTX = {"identity_id": "SYSTEM", "device_id": "SYS-01", "role": "admin", "realm": "SYSTEM"}
    identity_gateway.sessions["MOCK-SESSION-SALA-ADMIN"] = SYSTEM_CTX

    print("\n" + "="*40)
    print("      ORCA SOVEREIGN DASHBOARD (SALA)")
    print("="*40)

    try:
        response = client.get("/orca/dashboard/summary", headers=headers)
        if response.status_code == 200:
            data = response.json()
            metrics = data["metrics"]

            print(f"Status: {data['status']} | Node: {data['node_id']}")
            print(f"Audit Health: [{metrics['audit_status']}]")
            print("-" * 40)
            print(f"Total Bookings Today : {metrics['total_bookings_today']}")
            print(f"Total Revenue (MVR)  : {metrics['total_revenue_mvr']}")
            print(f"Synced Offline Recs  : {metrics['synced_offline_records']}")
            print("-" * 40)
        else:
            print(f"Error fetching dashboard: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Dashboard Error: {e}")

    print("="*40 + "\n")

if __name__ == "__main__":
    show_dashboard()
