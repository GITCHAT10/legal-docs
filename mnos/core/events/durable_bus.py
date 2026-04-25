class EventBus:
    def publish(self, island_id, event_type, payload): pass
    def replay(self, island_id): return [{"island_id": island_id}]
event_bus = EventBus()
