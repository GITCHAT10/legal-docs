class FaithEngine:
    def __init__(self, guard, fce, shadow, events):
        self.guard = guard
        self.fce = fce
        self.shadow = shadow
        self.events = events

    def record_donation(self, actor_ctx: dict, donation_data: dict):
        return self.guard.execute_sovereign_action(
            "imoxon.faith.donate",
            actor_ctx,
            self._internal_record_donation,
            donation_data
        )

    def _internal_record_donation(self, donation_data: dict):
        amount = donation_data.get("amount", 0)
        donation_type = donation_data.get("type", "SADAQAH")

        # Financial trace (Faith is usually tax-exempt in many contexts, but we log it)
        pricing = self.fce.price_order(amount)

        entry = {
            "user": self.guard.get_actor().get("identity_id"),
            "amount": amount,
            "type": donation_type,
            "pricing": pricing,
            "timestamp": "now"
        }
        self.events.publish("faith.donation_recorded", entry)
        return entry
