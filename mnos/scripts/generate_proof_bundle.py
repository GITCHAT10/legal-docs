import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List
from mnos.modules.aig_shadow.service import aig_shadow

def generate_merkle_witness_bundle(bundle_id: str):
    """
    Generates a cryptographic proof bundle for the SALA Live Cycle.
    Includes SHADOW audit entries and trace evidence.
    """
    chain = aig_shadow.chain

    # Filter for relevant events in the live cycle
    relevant_events = {
        "exmail.received",
        "nexus.guest.created",
        "nexus.reservation.confirmed",
        "ut.booking.created",
        "sala.invoice.finalized",
        "FINALIZE_INVOICE_PROCESS"
    }

    audit_trail = [e for e in chain if e["event_type"] in relevant_events]

    bundle = {
        "bundle_id": bundle_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "doctrine": "MIG-SALA-SOVEREIGN",
        "audit_trail": audit_trail,
        "chain_head_hash": chain[-1]["hash"] if chain else None,
        "chain_integrity": aig_shadow.verify_integrity()
    }

    bundle_json = json.dumps(bundle, indent=2, default=str)
    bundle_hash = hashlib.sha256(bundle_json.encode()).hexdigest()

    filename = f"mnos/proof_bundle_{bundle_id}.json"
    with open(filename, "w") as f:
        f.write(bundle_json)

    print(f"Proof Bundle '{bundle_id}' generated: {filename}")
    print(f"Bundle Hash: {bundle_hash}")
    return filename

if __name__ == "__main__":
    generate_merkle_witness_bundle('MIG-SALA-LIVE-CYCLE-2026')
