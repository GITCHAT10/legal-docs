class EventAdapter:
    def __init__(self, bus):
        self.bus = bus

    def trigger(self, event_name: str, payload: dict):
        self.bus.publish(f"imoxon.{event_name}", payload)

    def subscribe(self, event_name: str, callback):
        self.bus.subscribe(f"imoxon.{event_name}", callback)
