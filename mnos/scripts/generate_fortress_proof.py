import json
import os
from mnos.modules.shadow.service import shadow
from mnos.core.security.aegis import aegis
from mnos.shared.execution_guard import guard

def generate_proof():
    # 1. Setup session
    session = {"device_id": "MD_A096158_ROOT", "role": "privileged"}
    session["signature"] = aegis.sign_session(session)

    # 2. Add some event
    guard.execute_sovereign_action(
        "nexus.security.handshake",
        {"status": "FORTRESS_LOCK"},
        session,
        lambda p: "done"
    )

    # 3. Export Forensic Bundle
    bundle = shadow.export_forensic_bundle()
    bundle["bundle_id"] = "MIG-PR29-FORTRESS-PROOF"
    bundle["certificate_id"] = "MIG-COURT-VALID-2026"

    output_path = "mnos/MIG-PR29-FORTRESS-PROOF.json"
    with open(output_path, "w") as f:
        json.dump(bundle, f, indent=4)
    print(f"Proof bundle generated: {output_path}")

if __name__ == "__main__":
    generate_proof()
