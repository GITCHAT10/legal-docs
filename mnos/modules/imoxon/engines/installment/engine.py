class InstallmentEngine:
    def __init__(self, guard, fce, shadow, events):
        self.guard = guard
        self.fce = fce
        self.shadow = shadow
        self.events = events

    def create_plan(self, actor_ctx: dict, total_amount: float, months: int):
        return self.guard.execute_sovereign_action(
            "imoxon.installment.create",
            actor_ctx,
            self._internal_create_plan,
            total_amount, months
        )

    def _internal_create_plan(self, total_amount: float, months: int):
        pricing = self.fce.price_order(total_amount)
        final_total = pricing["total"]

        monthly = final_total / months
        schedule = [{"month": i+1, "amount": round(monthly, 2)} for i in range(months)]

        entry = {
            "user": self.guard.get_actor().get("identity_id"),
            "total": final_total,
            "schedule": schedule,
            "status": "ACTIVE"
        }
        self.events.publish("installment.created", entry)
        return entry
