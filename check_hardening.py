import os

with open('skyfarm/integration/router.py', 'r') as f:
    content = f.read()

checks = {
    "Timeout implemented": "timeout=5" in content,
    "Retry strategy implemented": "Retry(" in content,
    "Real HTTP status propagation": "raise HTTPException(status_code=resp.status_code" in content or "propagate real HTTP status" in content.lower(),
    "Traceability (correlation_id)": "X-Correlation-Id" in content
}

for check, passed in checks.items():
    print(f"{check}: {'PASS' if passed else 'FAIL'}")
