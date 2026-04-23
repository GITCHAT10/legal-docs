class DemandEngine:
    """
    Capture and Aggregate: Handles resort demand signals and batch formation.
    """
    def __init__(self, shadow, events):
        self.shadow = shadow
        self.events = events
        self.signals = []
        self.batches = {}

    def capture_signal(self, resort_id: str, items: list, urgency: str = "NORMAL"):
        signal_id = f"dem_{hash(resort_id + str(items)) % 10000}"
        signal = {
            "id": signal_id,
            "resort_id": resort_id,
            "items": items,
            "urgency": urgency,
            "status": "VALIDATED"
        }
        self.shadow.record_action("supply.demand_signal", signal)
        self.events.trigger("DEMAND_SIGNAL_VALIDATED", signal)
        self.signals.append(signal)
        return signal

    def form_batch(self, batch_id: str, signal_ids: list):
        items = []
        for sid in signal_ids:
            # Aggregate items logic here
            items.extend([s["items"] for s in self.signals if s["id"] == sid])

        batch = {"id": batch_id, "signals": signal_ids, "aggregated_items": items, "status": "LOCKED"}
        self.shadow.record_action("supply.batch_locked", batch)
        self.events.trigger("DEMAND_BATCH_LOCKED", batch)
        self.batches[batch_id] = batch
        return batch
