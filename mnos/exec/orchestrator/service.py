from typing import Dict, Any, Callable

class OrchestratorService:
    """
    SALA Node Orchestrator.
    Routes events between system modules.
    """
    def __init__(self, events):
        self.events = events
        self.handlers = {}

    def register_handler(self, event_type: str, handler: Callable):
        self.handlers[event_type] = handler

    def dispatch(self, event_type: str, payload: Dict[str, Any]):
        if event_type in self.handlers:
            self.handlers[event_type](payload)

        # Always publish to global bus
        self.events.publish(event_type, payload)
