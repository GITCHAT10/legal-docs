class DeliveryEngine:
    def __init__(self, guard, shadow, events):
        self.guard = guard
        self.shadow = shadow
        self.events = events
        self.manifests = {}

    def create_manifest(self, actor_ctx: dict, lot_ids: list, captain_id: str, resort_id: str):
        return self.guard.execute_sovereign_action(
            "imoxon.shipment.dispatch",
            actor_ctx,
            self._internal_create_manifest,
            lot_ids, captain_id, resort_id
        )

    def _internal_create_manifest(self, lot_ids: list, captain_id: str, resort_id: str):
        manifest_id = f"man_{hash(str(lot_ids) + captain_id) % 10000}"
        manifest = {
            "id": manifest_id,
            "lots": lot_ids,
            "captain": captain_id,
            "destination": resort_id,
            "status": "CREATED"
        }
        self.events.publish("shipment.dispatched", manifest)
        self.manifests[manifest_id] = manifest
        return manifest

    def confirm_resort_receipt(self, actor_ctx: dict, manifest_id: str, resort_id: str, items: list):
        return self.guard.execute_sovereign_action(
            "imoxon.shipment.receive",
            actor_ctx,
            self._internal_confirm_receipt,
            manifest_id, resort_id, items
        )

    def _internal_confirm_receipt(self, manifest_id: str, resort_id: str, items_accepted: list):
        confirmation = {
            "manifest_id": manifest_id,
            "resort_id": resort_id,
            "items": items_accepted,
            "status": "ACCEPTED"
        }
        self.events.publish("shipment.received", confirmation)
        if manifest_id in self.manifests:
            self.manifests[manifest_id]["status"] = "DELIVERED"
        return confirmation
