class SkygodownEngine:
    """
    Receive and Allocate: Handles inbound lots, QC, and allocation to resorts.
    """
    def __init__(self, shadow, events):
        self.shadow = shadow
        self.events = events
        self.lots = {}

    def receive_shipment(self, rfp_id: str, supplier_id: str, items: list):
        lot_id = f"lot_{rfp_id[:4]}_{hash(supplier_id) % 1000}"
        lot = {
            "id": lot_id,
            "rfp_id": rfp_id,
            "supplier": supplier_id,
            "items": items,
            "status": "RECEIVED",
            "qc_passed": False
        }
        self.shadow.commit("supply.lot_received", lot)
        self.events.publish("SKYGODOWN_RECEIVED", lot)
        self.lots[lot_id] = lot
        return lot

    def allocate_to_resort(self, lot_id: str, resort_id: str, quantities: dict):
        allocation = {"lot_id": lot_id, "resort_id": resort_id, "quantities": quantities, "status": "ALLOCATED"}
        self.shadow.commit("supply.lot_allocated", allocation)
        self.events.publish("LOT_ALLOCATED", allocation)
        return allocation
