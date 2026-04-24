from typing import Dict, Any, List
import logging
from datetime import datetime, UTC
import uuid

class EventBus:
    """
    Kafka-style Durable Event Bus for N-DEOS.
    Supports partitioning by island and replayability.
    """
    def __init__(self):
        self._store: Dict[str, List[Dict[str, Any]]] = {} # island_id -> events

    def publish(self, island_id: str, event_type: str, payload: Dict[str, Any]):
        event = {
            "id": str(uuid.uuid4()),
            "type": event_type,
            "island_id": island_id,
            "payload": payload,
            "timestamp": datetime.now(UTC).isoformat()
        }
        if island_id not in self._store:
            self._store[island_id] = []
        self._store[island_id].append(event)
        logging.info(f"EVENT BUS: Published {event_type} for {island_id}")

    def replay(self, island_id: str, since: str = None) -> List[Dict[str, Any]]:
        events = self._store.get(island_id, [])
        if since:
            return [e for e in events if e["timestamp"] > since]
        return events

event_bus = EventBus()
