class EscrowEngine:
    def __init__(self, guard, fce, shadow, events):
        self.guard = guard
        self.fce = fce
        self.shadow = shadow
        self.events = events

    def lock_funds(self, actor_ctx: dict, escrow_data: dict):
        return self.guard.execute_sovereign_action(
            "imoxon.escrow.lock",
            actor_ctx,
            self._internal_lock_funds,
            escrow_data
        )

    def _internal_lock_funds(self, escrow_data: dict):
        amount = escrow_data.get("amount", 0)
        pricing = self.fce.price_order(amount)

        entry = {
            "escrow_id": f"esc_{hash(str(escrow_data)) % 10000}",
            "depositor": self.guard.get_actor().get("identity_id"),
            "target": escrow_data.get("target"),
            "pricing": pricing,
            "status": "LOCKED"
        }
        self.events.publish("escrow.funds_locked", entry)
        return entry
