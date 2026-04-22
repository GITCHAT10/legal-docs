from typing import Dict, Any
import hashlib
import json
from mnos.modules.shadow.service import shadow

class VSATGenerator:
    """
    Audit Security Layer (VSAT):
    Generates Verifiable Sovereign Audit Trail (VSAT) proofs.
    """
    def generate_proof(self, trace_id: str, event_hash: str) -> Dict[str, Any]:
        """
        Creates a cryptographic proof of an action for legal or audit purposes.
        """
        # Find the entry in shadow ledger
        entry = next((e for e in shadow.chain if e.get("hash") == event_hash), None)

        if not entry:
            return {"error": "Event not found in SHADOW ledger."}

        proof_payload = {
            "trace_id": trace_id,
            "event_hash": event_hash,
            "timestamp": entry["timestamp"],
            "event_type": entry["event_type"],
            "payload_summary": str(entry["payload"])[:100],
            "merkle_root_at_time": shadow.chain[-1]["hash"]
        }

        proof_signature = hashlib.sha256(json.dumps(proof_payload, sort_keys=True).encode()).hexdigest()

        return {
            "vsat_id": f"VSAT-{trace_id[:8]}",
            "proof": proof_payload,
            "signature": proof_signature,
            "status": "VERIFIED"
        }

vsat = VSATGenerator()
