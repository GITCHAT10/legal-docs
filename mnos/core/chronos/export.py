import json
from typing import Dict, Any

class ProofBundleExport:
    """
    CHRONOS Export: Portable Verification Bundles.
    Includes everything needed to verify a decision externally.
    """
    def generate_bundle(self, trace_id: str, events: list, policy: dict):
        bundle = {
            "version": "v1-canonical",
            "trace_id": trace_id,
            "ordered_events": events,
            "policy_snapshot": policy,
            "schema_spec": "canonical_schema_spec_v1",
            "mmr_spec": "mmr_spec_v1"
        }
        return json.dumps(bundle, sort_keys=True)

bundle_exporter = ProofBundleExport()
