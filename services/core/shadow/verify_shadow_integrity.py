import requests
import sys
import os
import json

def verify():
    shadow_url = os.getenv("SHADOW_URL", "http://localhost:8002")
    try:
        resp = requests.get(f"{shadow_url}/verify-integrity")
        if resp.status_code == 200:
            result = resp.json()
            if result["status"] == "valid":
                print(f"✅ SHADOW LEDGER INTEGRITY VERIFIED: {result['count']} entries.")
                sys.exit(0)
            else:
                print(f"❌ SHADOW LEDGER CORRUPTED: {json.dumps(result['errors'], indent=2)}")
                sys.exit(1)
        else:
            print(f"❌ ERROR: SHADOW service returned {resp.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: Could not connect to SHADOW service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify()
