class SkygodownManager:
    def __init__(self, guard, shadow, events):
        self.guard = guard
        self.shadow = shadow
        self.events = events

    def receive_lot(self, actor_ctx: dict, lot_data: dict):
        return self.guard.execute_sovereign_action(
            "imoxon.shipment.receive",
            actor_ctx,
            self._internal_receive,
            lot_data
        )

    def _internal_receive(self, data):
        lot_id = f"lot_{hash(str(data)) % 10000}"
        lot = {
            "id": lot_id,
            "data": data,
            "status": "RECEIVED"
        }
        self.events.publish("SKYGODOWN_RECEIVED", lot)
        return lot
