import uuid
from datetime import datetime, UTC

class ResortWeeklyOrderSystem:
    """
    RESORT_WEEKLY_ORDER_SYSTEM (RC1-PRODUCTION-BRIDGE)
    Models the resort supply pipeline for automated weekly ordering.
    """
    def __init__(self, procurement_engine):
        self.procurement = procurement_engine
        self.schedules = {} # resort_id -> schedule

    def register_weekly_schedule(self, resort_id: str, items: list, day_of_week: int):
        self.schedules[resort_id] = {
            "items": items,
            "day": day_of_week,
            "last_run": None
        }
        return {"status": "SCHEDULED", "resort": resort_id}

    def trigger_weekly_run(self, actor_ctx: dict, resort_id: str):
        if resort_id not in self.schedules:
             raise ValueError("Resort not registered")

        sched = self.schedules[resort_id]
        # Auto-create Purchase Request
        pr = self.procurement.create_purchase_request(
            actor_ctx,
            sched["items"],
            sum(i.get("est_price", 0) for i in sched["items"])
        )
        sched["last_run"] = datetime.now(UTC).isoformat()
        return pr
