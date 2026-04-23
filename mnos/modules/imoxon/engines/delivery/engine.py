class DeliveryEngine:
    """
    Deliver and Settle: Handles manifests and receipt confirmation.
    """
    def __init__(self, shadow, events):
        self.shadow = shadow
        self.events = events
        self.manifests = {}

    def create_manifest(self, lot_ids: list, captain_id: str, resort_id: str):
        manifest_id = f"man_{hash(str(lot_ids) + captain_id) % 10000}"
        manifest = {
            "id": manifest_id,
            "lots": lot_ids,
            "captain": captain_id,
            "destination": resort_id,
            "status": "CREATED"
        }
        self.shadow.record_action("supply.manifest_created", manifest)
        self.events.trigger("MANIFEST_CREATED", manifest)
        self.manifests[manifest_id] = manifest
        return manifest

    def confirm_resort_receipt(self, manifest_id: str, resort_id: str, items_accepted: list):
        confirmation = {
            "manifest_id": manifest_id,
            "resort_id": resort_id,
            "items": items_accepted,
            "status": "ACCEPTED"
        }
        self.shadow.record_action("supply.receipt_accepted", confirmation)
        self.events.trigger("RESORT_RECEIPT_ACCEPTED", confirmation)
        if manifest_id in self.manifests:
            self.manifests[manifest_id]["status"] = "DELIVERED"
        return confirmation
