import json
import hashlib
from typing import Dict, Any, List

class SemanticAudit:
    """
    MIG-ONTOLOGY-GOVERNANCE: Semantic Audit Hardening.
    Enforces canonical field sets for reasoning traces.
    """
    def compute_canonical_hash(self, trace_data: Dict[str, Any]) -> str:
        """Enforces canonical schema spec v1."""
        # Requirements: trace_id, decision, evidence_refs, policy_id, timestamp
        canonical_fields = [
            'trace_id',
            'decision',
            'evidence_refs',
            'policy_id',
            'timestamp'
        ]

        data = {k: trace_data.get(k) for k in canonical_fields}

        # Enforce strict UTF-8 and deterministic serialization
        block_string = json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')
        return hashlib.sha256(block_string).hexdigest()

semantic_audit = SemanticAudit()
