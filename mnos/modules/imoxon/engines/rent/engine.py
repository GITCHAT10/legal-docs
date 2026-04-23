class RentEngine:
    def __init__(self, guard, fce, shadow, events):
        self.guard = guard
        self.fce = fce
        self.shadow = shadow
        self.events = events

    def create_lease(self, actor_ctx: dict, lease_data: dict):
        return self.guard.execute_sovereign_action(
            "imoxon.rent.lease",
            actor_ctx,
            self._internal_create_lease,
            lease_data
        )

    def _internal_create_lease(self, lease_data: dict):
        rent_amount = lease_data.get("rent", 0)
        # Rent logic: Apply tax/SC per property rules
        pricing = self.fce.price_order(rent_amount)

        entry = {
            "tenant": self.guard.get_actor().get("identity_id"),
            "property": lease_data.get("property"),
            "pricing": pricing,
            "status": "LEASE_SIGNED"
        }
        self.events.publish("rent.lease_created", entry)
        return entry
