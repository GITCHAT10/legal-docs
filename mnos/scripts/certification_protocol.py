import json
import os
import sys
from datetime import datetime, timezone

# Add parent directory to path to allow imports from mnos
sys.path.append(os.getcwd())

import time
from mnos.core.apollo.health_monitor import cold_watch
from mnos.core.aig_aegis.service import aig_aegis

def run_protocol():
    log = []
    print("--- MNOS RC1 CERTIFICATION PROTOCOL START ---")

    # Phase 1: Zero-Point Hold (Simulation Hour 20 to 24)
    for hour in range(20, 25):
        cold_watch.current_hour = hour
        report = cold_watch.emit_hourly_report(hour)
        log.append(report)

        if hour == 24:
            print("--- HOUR 24 REACHED: TRIGGERING CERTIFICATION ---")

            # Prepare signed session for CEO-REGISTRY
            session = {
                "device_id": "CEO-REGISTRY",
                "biometric_verified": True,
                "nonce": f"cert-nonce-{time.time()}",
                "timestamp": int(time.time())
            }
            session["signature"] = aig_aegis.sign_session(session)

            cert = cold_watch.trigger_certification(session_context=session)
            if cert:
                log.append({"event": "CERTIFIED", "data": cert})
            else:
                print("CERTIFICATION FAILED")
                sys.exit(1)

    with open("mnos/CERTIFICATION_EVENT_LOG.json", "w") as f:
        json.dump(log, f, indent=2)

    print("--- PROTOCOL COMPLETE: CERTIFICATION_EVENT_LOG.json generated ---")

if __name__ == "__main__":
    run_protocol()
