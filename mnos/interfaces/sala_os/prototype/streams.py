from typing import List, Callable
from mnos.core.events.service import events

class SalaStreamHandler:
    """
    SALA-OS WebSocket Stream Integration (Simulated).
    Subscribes to MNOS real-time operational events.
    """
    def __init__(self):
        self.active_channels = ["/ws/operations"]
        self._register_subscribers()

    def _register_subscribers(self):
        # Bind to core events for real-time UI updates
        events.subscribe("nexus.guest.arrival", self.on_arrival_update)
        # Note: ROOM_STATUS_CHANGE, FOLIO_POST, HK_TASK_UPDATE added to taxonomy in production
        print("[SALA-STREAMS] WebSocket handlers registered for operations channel.")

    def on_arrival_update(self, payload):
        print(f"[SALA-UI-WS] Real-time ARRIVAL_UPDATE received: {payload.get('trace_id')}")

    def on_room_status_change(self, payload):
        print(f"[SALA-UI-WS] Real-time ROOM_STATUS_CHANGE received.")

sala_streams = SalaStreamHandler()
