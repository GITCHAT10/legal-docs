class ProcurementEngine:
    def __init__(self, guard, shadow, events):
        self.guard = guard
        self.shadow = shadow
        self.events = events

    def issue_rfp(self, actor_ctx: dict, signal_ids: list):
        return self.guard.execute_sovereign_action(
            "imoxon.rfp.issue",
            actor_ctx,
            self._internal_issue_rfp,
            signal_ids
        )

    def _internal_issue_rfp(self, signal_ids):
        rfp_id = f"rfp_{hash(str(signal_ids)) % 10000}"
        rfp = {
            "id": rfp_id,
            "signals": signal_ids,
            "status": "ISSUED"
        }
        self.events.publish("RFP_ISSUED", rfp)
        return rfp

    def award_bid(self, actor_ctx: dict, rfp_id: str, supplier_id: str):
        return self.guard.execute_sovereign_action(
            "imoxon.bid.accept",
            actor_ctx,
            self._internal_award,
            rfp_id, supplier_id
        )

    def _internal_award(self, rfp_id, supplier_id):
        award = {
            "rfp_id": rfp_id,
            "supplier_id": supplier_id,
            "status": "AWARDED"
        }
        self.events.publish("SUPPLIER_AWARDED", award)
        return award
