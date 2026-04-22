import asyncio
import logging
from datetime import datetime, UTC

class EventEngine:
    """
    MNOS Event Engine
    Event-driven architecture for system-wide triggers and orchestration.
    """
    def __init__(self):
        self.subscribers = {}
        self.history = []

    def subscribe(self, event_type: str, callback):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    async def emit(self, event_type: str, payload: dict):
        timestamp = datetime.now(UTC).isoformat()
        event_data = {
            "event_type": event_type,
            "payload": payload,
            "timestamp": timestamp
        }
        self.history.append(event_data)

        if event_type in self.subscribers:
            tasks = [callback(payload) for callback in self.subscribers[event_type]]
            if tasks:
                await asyncio.gather(*tasks)

        logging.info(f"Event Emitted: {event_type}")

event_engine = EventEngine()
