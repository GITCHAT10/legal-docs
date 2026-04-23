class ProcurementEngine:
    """
    Procure: Handles RFPs, supplier bids, and award flows.
    """
    def __init__(self, shadow, events):
        self.shadow = shadow
        self.events = events
        self.rfps = {}
        self.bids = {}

    def create_rfp(self, rfp_id: str, batch_id: str, items: list, suppliers: list):
        rfp = {"id": rfp_id, "batch_id": batch_id, "items": items, "recipients": suppliers, "status": "OPEN"}
        self.shadow.record_action("supply.rfp_created", rfp)
        self.events.trigger("RFP_OPENED", rfp)
        self.rfps[rfp_id] = rfp
        return rfp

    def submit_bid(self, supplier_id: str, rfp_id: str, total_price: float):
        bid = {"supplier": supplier_id, "rfp": rfp_id, "price": total_price, "timestamp": "now"}
        self.shadow.record_action("supply.bid_submitted", bid)
        self.events.trigger("BID_SUBMITTED", bid)
        self.bids[rfp_id] = self.bids.get(rfp_id, []) + [bid]
        return bid

    def award_rfp(self, rfp_id: str, supplier_id: str):
        award = {"rfp_id": rfp_id, "supplier_id": supplier_id, "status": "AWARDED"}
        self.shadow.record_action("supply.rfp_awarded", award)
        self.events.trigger("SUPPLIER_AWARDED", award)
        if rfp_id in self.rfps:
            self.rfps[rfp_id]["status"] = "AWARDED"
        return award
