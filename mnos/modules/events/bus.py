from collections import defaultdict
from datetime import datetime, UTC

class EventBus:
    """
    EVENTS: System-wide orchestration brain.
    """
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.history = []

    def subscribe(self, event_type: str, callback):
        self.subscribers[event_type].append(callback)

    def publish(self, event_type: str, payload: dict):
        event = {
            "type": event_type,
            "payload": payload,
            "timestamp": datetime.now(UTC).isoformat()
        }
        self.history.append(event)

        print(f"[EVENT] {event_type} published.")

        for callback in self.subscribers[event_type]:
            try:
                callback(payload)
            except Exception as e:
                print(f"[ERROR] Event callback failed: {e}")

    def get_history(self):
        return self.history
