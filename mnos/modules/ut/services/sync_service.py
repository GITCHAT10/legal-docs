import uuid
from typing import Dict

class UTAPOLLOSyncService:
    def __init__(self, shadow, events):
        self.shadow = shadow
        self.events = events
        self.offline_queue = []
        self.processed_ids = set()

    def queue_offline_event(self, actor_ctx: dict, event_data: dict):
        """
        Queues an event for later replay when online.
        """
        event_id = str(uuid.uuid4())
        event = {
            "event_id": event_id,
            "actor": actor_ctx,
            "payload": event_data,
            "status": "QUEUED"
        }
        self.offline_queue.append(event)
        return event_id

    def replay_sync(self) -> Dict:
        """
        Replays queued events with idempotency and signature validation.
        """
        results = []
        for event in self.offline_queue:
            if event["event_id"] in self.processed_ids:
                continue

            # Signature validation simulation
            if not event["actor"].get("identity_id"):
                results.append({"event_id": event["event_id"], "status": "FAILED", "reason": "Missing Identity"})
                continue

            # Process event
            event["status"] = "SYNCED"
            self.processed_ids.add(event["event_id"])

            # Log to SHADOW
            self.shadow.commit("ut.apollo.sync_replay", event["actor"]["identity_id"], event)
            results.append({"event_id": event["event_id"], "status": "SUCCESS"})

        self.offline_queue = [e for e in self.offline_queue if e["status"] != "SYNCED"]
        return {"processed_count": len(results), "results": results}

    def is_synced(self, trace_id: str) -> bool:
        """
        Checks if all events for a trace_id are synced.
        """
        for event in self.offline_queue:
            if event["payload"].get("trace_id") == trace_id:
                return False
        return True
