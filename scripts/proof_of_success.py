import asyncio
import os
import json
import uuid
import time
from mnos.shared.sdk.client import MnosClient

async def run_proof():
    print("--- MNOS LIFELINE End-to-End Proof ---")
    os.environ["MNOS_INTEGRATION_SECRET"] = "top-secret"

    # Base URL for gateway
    client = MnosClient("http://localhost:8000")

    transaction_id = str(uuid.uuid4())
    print(f"Transaction ID: {transaction_id}")

    patient_data = {
        "name": "Ahmed Mohamed",
        "national_id": "A123456",
        "dob": "1990-01-01"
    }

    try:
        # 1. Verification (AEGIS)
        print("1. Verifying via AEGIS...")
        aegis_success = await client.verify_aegis("valid_token", "CREATE", "PATIENT")
        print(f"   AEGIS Response: {aegis_success}")

        # 2. Decision (ELEONE)
        print("2. Processing via ELEONE...")
        decision, policy_decision_id = await client.decide_eleone({"action": "CREATE_PATIENT", "data": patient_data})
        print(f"   ELEONE Decision: {decision}, Policy ID: {policy_decision_id}")

        # 3. Execution (LIFELINE) - Simulating the module logic
        print("3. Writing to LIFELINE (Simulated)...")
        # In a real flow, we'd hit the /api/lifeline/patients endpoint which does all this
        # But for proof of core components:

        # 4. Event (EVENTS)
        print("4. Publishing Event...")
        event_id = await client.publish_event("PATIENT_CREATED", {"patient_id": "PAT-123"})
        print(f"   EVENT ID: {event_id}")

        # 5. Commit (SHADOW)
        print("5. Committing to SHADOW...")
        shadow_id = await client.commit_shadow(transaction_id, event_id, patient_data)
        print(f"   SHADOW Record ID: {shadow_id}")

        # 6. Billing (FCE)
        print("6. Calculating via FCE...")
        billing_data = {
            "items": [{"code": "CONSULT", "price": 500.0}],
            "patient_id": "PAT-123"
        }
        fce_result = await client.calculate_fce(billing_data)
        print(f"   FCE Result: {json.dumps(fce_result, indent=2)}")

        print("\n--- Summary of Proof ---")
        print(f"Transaction ID: {transaction_id}")
        print(f"Event ID: {event_id}")
        print(f"Shadow ID: {shadow_id}")
        print(f"Policy ID: {policy_decision_id}")
        print("Status: SUCCESS")

    except Exception as e:
        print(f"Trace Failed: {e}")
        return False
    return True

if __name__ == "__main__":
    asyncio.run(run_proof())
