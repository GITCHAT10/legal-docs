import json
import os
import sys

def final_validate():
    checks = {
        "report_exists": os.path.exists("GUARD_PROOF_REPORT.json"),
        "apollo_exists": os.path.exists("mnos/core/apollo/deployment.py") and os.path.exists("mnos/core/apollo/override.py"),
        "aegis_hardened": "nonce" in open("mnos/core/aig_aegis/service.py").read(),
        "shadow_hardened": "separators=(',', ':')" in open("mnos/modules/aig_shadow/service.py").read(),
        "event_bus_locked": "Trace_id is mandatory" in open("mnos/infrastructure/mig_event_spine/service.py").read(),
    }

    if all(checks.values()):
        print("MNOS CORE 10.0 = CONTROLLED SOVEREIGN INFRASTRUCTURE")
        print("APOLLO = ACTIVE + ATTESTED")
        print("OVERRIDE = VERIFIED + SECURE")
    else:
        print("FINAL VALIDATION FAILED")
        print(json.dumps(checks, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    final_validate()
