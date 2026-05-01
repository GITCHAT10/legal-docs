class UTAMEvents:
    """
    UT AEROMARINE Event Handlers.
    Maps mission events to the MNOS Distributed Event Bus.
    """
    def __init__(self, event_bus):
        self.bus = event_bus

    def publish_mission_event(self, event_type: str, payload: dict):
        self.bus.publish(f"utam.mission.{event_type.lower()}", payload)
