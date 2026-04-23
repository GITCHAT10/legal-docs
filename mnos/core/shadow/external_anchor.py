from mnos.modules.shadow.service import shadow
import json

class ExternalAnchor:
    """
    SHADOW External Anchor.
    Prepares hashes for public timestamping.
    Mode: HASH_EXPORT_ONLY
    """
    def export_latest_hash(self):
        """Exports the latest ledger hash for external anchoring."""
        if not shadow.chain:
            return None

        latest = shadow.chain[-1]
        return {
            "entry_id": latest["entry_id"],
            "hash": latest["hash"],
            "timestamp": latest["timestamp"],
            "version": "MIG-SOVEREIGN-9.5"
        }

external_anchor = ExternalAnchor()
