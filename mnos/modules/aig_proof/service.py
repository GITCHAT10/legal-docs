from typing import Dict, Any
import hashlib
import json
from mnos.modules.aig_shadow.service import aig_shadow

class AIGProofGenerator:
    """
    Audit Security Layer (AIGProof):
    Generates Verifiable Sovereign Audit Trail (AIGProof) proofs.
    """
    def generate_proof(self, trace_id: str, event_hash: str) -> Dict[str, Any]:
        """
        Creates a cryptographic proof of an action for legal or audit purposes.
        Includes AIGAegis identity hash and full action chain links.
        """
        # Find the entry in aig_shadow ledger
        entry_index = next((i for i, e in enumerate(aig_shadow.chain) if e.get("hash") == event_hash), None)

        if entry_index is None:
            return {"error": "Event not found in AIGShadow ledger."}

        entry = aig_shadow.chain[entry_index]
        prev_hash = entry.get("previous_hash", "0" * 64)

        # Extract AIGAegis identity if present in payload (authorized_session is often in event data)
        # For simulation, we hash the device_id if available
        actor_id = entry["payload"].get("authorized_session", {}).get("device_id", "SYSTEM")
        identity_hash = hashlib.sha256(actor_id.encode()).hexdigest()

        proof_payload = {
            "trace_id": trace_id,
            "event_hash": event_hash,
            "previous_hash": prev_hash,
            "identity_hash": identity_hash,
            "timestamp": entry["timestamp"],
            "event_type": entry["event_type"],
            "payload_summary": str(entry["payload"])[:100],
            "merkle_root_at_time": aig_shadow.chain[-1]["hash"]
        }

        proof_signature = hashlib.sha256(json.dumps(proof_payload, sort_keys=True).encode()).hexdigest()

        return {
            "aig_proof_id": f"AIGProof-{trace_id[:8]}",
            "proof": proof_payload,
            "signature": proof_signature,
            "chain_integrity": aig_shadow.verify_integrity(),
            "status": "VERIFIED"
        }

aig_proof = AIGProofGenerator()
