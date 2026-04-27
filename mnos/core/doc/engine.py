import hashlib
import json
from datetime import datetime, UTC
from typing import Dict, Any

class SigDocEngine:
    """
    SIG.DOC: Sovereign Document Sealing & Verification.
    Ensures immutability of digital documents via SHADOW anchors.
    """
    def __init__(self, shadow):
        self.shadow = shadow

    def seal_document(self, actor_id: str, document_type: str, data: Dict[str, Any]) -> str:
        # 1. Create canonical representation
        payload = {
            "document_type": document_type,
            "content": data,
            "timestamp": datetime.now(UTC).isoformat()
        }
        canonical_json = json.dumps(payload, sort_keys=True)

        # 2. Generate Seal (SHA-256)
        seal_hash = hashlib.sha256(canonical_json.encode()).hexdigest()

        # 3. Commit to SHADOW (ANCHOR)
        # Mandatory anchor for SIG.DOC
        self.shadow.commit(f"sigdoc.anchor", actor_id, {
            "document_type": document_type,
            "seal": seal_hash,
            "timestamp": payload["timestamp"]
        })

        return seal_hash

    def verify_seal(self, seal_hash: str, document_data: Dict[str, Any]) -> bool:
        # In a real system, we'd query SHADOW for this seal
        # For simulation, we check if the hash matches the data
        canonical_json = json.dumps(document_data, sort_keys=True)
        return hashlib.sha256(canonical_json.encode()).hexdigest() == seal_hash
