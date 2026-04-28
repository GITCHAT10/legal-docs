import hashlib
import json
from datetime import datetime, UTC
from typing import Dict, Any

class SigDocEngine:
    """
    SIG.DOC Sovereign Document Sealing Engine.
    Implements immutable sealing of digital records anchored to SHADOW.
    """
    def __init__(self, shadow):
        self.shadow = shadow

    def seal_document(self, doc_type: str, content: Dict[str, Any], actor_id: str, trace_id: str) -> str:
        """
        Generates a SHA-256 seal for a document and anchors it to the SHADOW ledger.
        """
        canonical_payload = {
            "type": doc_type,
            "content": content,
            "timestamp": datetime.now(UTC).isoformat()
        }

        # Calculate Hash
        payload_string = json.dumps(canonical_payload, sort_keys=True).encode()
        doc_hash = hashlib.sha256(payload_string).hexdigest()

        # Anchor to SHADOW
        self.shadow.commit(
            event_type=f"sigdoc.sealed.{doc_type}",
            actor_id=actor_id,
            payload={
                "doc_hash": doc_hash,
                "doc_type": doc_type,
                "canonical_content": content
            },
            trace_id=trace_id
        )

        return doc_hash

    def verify_seal(self, doc_hash: str) -> bool:
        """
        Verifies if a seal exists in the SHADOW ledger and is valid.
        """
        for block in self.shadow.chain:
            if block.get("payload", {}).get("doc_hash") == doc_hash:
                return True
        return False
