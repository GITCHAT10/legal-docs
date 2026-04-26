import uuid
from mnos.modules.shadow.ledger import ShadowLedger

class ShadowEventEmitter:
    """
    Forensic Shadow-Linked Event Emitter.
    Ensures every event is backed by a SHADOW commit.
    """
    def __init__(self, shadow: ShadowLedger, events):
        self.shadow = shadow
        self.events = events

    def emit(self, event_type: str, actor_id: str, payload: dict):
        # 1. Commit to SHADOW (Requires ExecutionGuard context)
        shadow_ref = self.shadow.commit(f"event.{event_type}", actor_id, payload)

        # 2. Enrich payload with shadow reference
        enriched_payload = {
            **payload,
            "shadow_ref": shadow_ref,
            "forensic_id": uuid.uuid4().hex[:8]
        }

        # 3. Publish to System Bus
        self.events.publish(event_type, enriched_payload)
        return shadow_ref
