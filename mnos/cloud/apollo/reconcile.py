from typing import Dict, List, Any

class ShadowReconciler:
    """
    APOLLO: SHADOW Hash Reconciliation.
    Detects state conflicts and enforces financial locks on mismatch.
    """
    def __init__(self, shadow_ledger, fce_engine):
        self.shadow = shadow_ledger
        self.fce = fce_engine
        self.conflicts = []

    def reconcile_with_remote(self, remote_node_id: str, remote_ledger_summary: List[dict]):
        """
        Compares local SHADOW chain against remote summary.
        """
        local_summary = [{"index": b["index"], "hash": b["hash"]} for b in self.shadow.chain]

        for remote_block in remote_ledger_summary:
            idx = remote_block["index"]
            if idx < len(local_summary):
                if local_summary[idx]["hash"] != remote_block["hash"]:
                    self._handle_mismatch(remote_node_id, idx)

    def _handle_mismatch(self, node_id: str, index: int):
        conflict = {"node_id": node_id, "index": index, "status": "CONFLICT_DETECTED"}
        self.conflicts.append(conflict)

        # Rule: financial mismatch = lock FCE settlement
        print(f"[RECONCILE] CRITICAL: SHADOW Mismatch at block {index} from {node_id}")
        if hasattr(self.fce, "lock_settlement"):
            self.fce.lock_settlement(f"SHADOW_CONFLICT_{node_id}_{index}")

        return conflict

    def get_conflict_report(self) -> List[dict]:
        return self.conflicts
