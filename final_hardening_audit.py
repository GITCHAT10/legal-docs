import os

def audit_router():
    with open('skyfarm/integration/router.py', 'r') as f:
        c = f.read()
    print(f"Router - Propagate real HTTP status: {'raise HTTPException(status_code=resp.status_code' in c}")
    print(f"Router - Enforce 5s timeout: {'timeout=5' in c}")
    print(f"Router - Retry strategy: {'Retry(' in c}")

def audit_secrets():
    for path in ['mnos/security.py', 'skyfarm/integration/service.py']:
        with open(path, 'r') as f:
            c = f.read()
        print(f"Secret Hardening ({path}) - Fail Fast: {'raise RuntimeError' in c}")

def audit_outbox():
    with open('skyfarm/integration/outbox_worker.py', 'r') as f:
        c = f.read()
    print(f"Outbox - Retry Strategy: {'Retry(' in c}")
    print(f"Outbox - Timeout: {'timeout=5' in c}")

audit_router()
audit_secrets()
audit_outbox()
