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

    def seal_document(self, actor_id: str, document_type: str, data: Dict[str, Any]) -> dict:
        # 1. Create canonical representation
        timestamp = datetime.now(UTC).isoformat()
        payload = self._build_canonical_payload(document_type, data, timestamp)
        canonical_json = json.dumps(payload, sort_keys=True)

        # 2. Generate Seal (SHA-256)
        seal_hash = hashlib.sha256(canonical_json.encode()).hexdigest()

        # 3. Commit to SHADOW (ANCHOR)
        # Mandatory anchor for SIG.DOC
        self.shadow.commit(f"sigdoc.anchor", actor_id, {
            "document_type": document_type,
            "seal": seal_hash,
            "timestamp": timestamp
        })

        return {"seal": seal_hash, "timestamp": timestamp}

    def verify_seal(self, seal_hash: str, document_type: str, document_data: Dict[str, Any], timestamp: str) -> bool:
        # Reconstruct canonical payload for verification
        payload = self._build_canonical_payload(document_type, document_data, timestamp)
        canonical_json = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(canonical_json.encode()).hexdigest() == seal_hash

    def _build_canonical_payload(self, doc_type: str, content: Dict[str, Any], timestamp: str) -> Dict[str, Any]:
        return {
            "document_type": doc_type,
            "content": content,
            "timestamp": timestamp
        }
