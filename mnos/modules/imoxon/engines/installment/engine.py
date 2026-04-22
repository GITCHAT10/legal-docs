class InstallmentEngine:
    def __init__(self, fce, shadow, events):
        self.fce = fce
        self.shadow = shadow
        self.events = events
        self.plans = {}

    def create_bnpl_plan(self, user_id: str, total_amount: float, months: int):
        schedule = []
        monthly = total_amount / months
        for i in range(1, months + 1):
            schedule.append({"month": i, "amount": round(monthly, 2), "status": "PENDING"})

        plan_id = f"inst_{hash(user_id + str(total_amount)) % 10000}"
        plan = {
            "plan_id": plan_id,
            "user_id": user_id,
            "total": total_amount,
            "schedule": schedule,
            "status": "ACTIVE"
        }

        self.shadow.record_action("installment.created", plan)
        self.events.trigger("INSTALLMENT_CREATED", plan)
        self.plans[plan_id] = plan
        return plan
