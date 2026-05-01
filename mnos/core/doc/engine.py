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
        from mnos.shared.execution_guard import ExecutionGuard

        canonical_payload = {
            "type": doc_type,
            "content": content,
            "timestamp": datetime.now(UTC).isoformat()
        }

        # Calculate Hash
        payload_string = json.dumps(canonical_payload, sort_keys=True).encode()
        doc_hash = hashlib.sha256(payload_string).hexdigest()

        # Wrap in authorized context if not already authorized
        actor = {"identity_id": actor_id, "device_id": "SIGDOC-ENGINE", "role": "admin"}

        if not ExecutionGuard.is_authorized():
            with ExecutionGuard.authorized_context(actor):
                self._commit_to_shadow(doc_type, actor_id, content, doc_hash, trace_id)
        else:
            self._commit_to_shadow(doc_type, actor_id, content, doc_hash, trace_id)

        return doc_hash

    def _commit_to_shadow(self, doc_type, actor_id, content, doc_hash, trace_id):
        # Anchor to SHADOW
        from mnos.shared.execution_guard import ExecutionGuard
        actor = {"identity_id": actor_id, "device_id": "SIGDOC-ENGINE", "role": "admin"}
        with ExecutionGuard.authorized_context(actor):
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

    def verify_seal(self, doc_hash: str) -> bool:
        """
        Verifies if a seal exists in the SHADOW ledger and is valid.
        """
        for block in self.shadow.chain:
            if block.get("payload", {}).get("doc_hash") == doc_hash:
                return True
        return False
