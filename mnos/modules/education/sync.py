import hashlib
import json
from datetime import datetime, UTC

class AcademySyncEngine:
    """
    Sync Engine for MARS Hospitality Academy.
    Ensures that offline training events on EDGE nodes are synchronized with the SHADOW ledger.
    Includes conflict resolution and high-reliability deduplication.
    """
    def __init__(self, core, education_engine):
        self.core = core
        self.edu = education_engine
        self.sync_logs = []
        self.processed_event_ids = set() # Idempotency guard

    def process_edge_sync(self, edge_node_id: str, events: list):
        """
        Processes a batch of education events from an EDGE node.
        """
        from mnos.shared.execution_guard import _sovereign_context
        results = []

        # [MAC EOS HARDENING] Reject if edge_node_id is missing
        if not edge_node_id:
             return [{"status": "FAILED", "reason": "INVALID_EDGE_NODE_ID"}]

        for event in events:
            event_id = event.get("id")

            # [MAC EOS HARDENING] Check for mandatory fields
            if not event_id:
                results.append({"status": "FAILED", "reason": "INVALID_EDGE_EVENT", "detail": "Missing event ID"})
                continue

            # [MAC EOS HARDENING] Namespace deduplication key
            dedup_key = f"{edge_node_id}:{event_id}"

            # 1. Idempotency Check
            if dedup_key in self.processed_event_ids:
                results.append({"event_id": event_id, "status": "SKIPPED", "reason": "ALREADY_PROCESSED"})
                continue

            # 2. Verify Event Integrity
            event_data = event.get("data")
            event_hash = event.get("hash")
            calculated_hash = hashlib.sha256(json.dumps(event_data, sort_keys=True).encode()).hexdigest()

            if event_hash != calculated_hash:
                results.append({"event_id": event_id, "status": "REJECTED", "reason": "HASH_MISMATCH"})
                continue

            # 3. Replay Action in Core
            action_type = event.get("action_type")
            actor_ctx = event.get("actor_ctx")

            # Enrich actor context with system_override and trace
            sync_actor = {
                **actor_ctx,
                "token": f"SYNC-{edge_node_id}-{event_id}",
                "system_override": True
            }

            try:
                # Set sovereign context for sync operation
                token = _sovereign_context.set({
                    "token": sync_actor["token"],
                    "actor": sync_actor
                })

                try:
                    # Direct commit to SHADOW to preserve forensic timeline
                    self.core.shadow.commit(
                        f"edge_sync.{action_type}",
                        actor_ctx.get("identity_id"),
                        {
                            "edge_node": edge_node_id,
                            "original_timestamp": event.get("timestamp"),
                            "payload": event_data,
                            "sync_v": "1.2"
                        }
                    )

                    # 4. Conflict Resolution & State Application
                    if action_type == "education.assessment.submit":
                         self.edu.submit_assessment(sync_actor, event_data)

                    self.processed_event_ids.add(dedup_key)
                    results.append({"event_id": event_id, "status": "SYNCED"})
                finally:
                    _sovereign_context.reset(token)

            except Exception as e:
                results.append({"event_id": event_id, "status": "FAILED", "reason": str(e)})

        self.sync_logs.append({
            "edge_node": edge_node_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "event_count": len(events),
            "results": results
        })

        return results
