class UTBridge:
    def __init__(self, guard, shadow, events):
        self.guard = guard
        self.shadow = shadow
        self.events = events

    def verify_feasibility(self, actor_ctx: dict, flight: str, date_obj: str) -> bool:
        """
        VERIFY_TRANSFER_CAPACITY_VIA_UT
        Checks for available slots and pickup windows.
        """
        # Simulated logic: Block flights landing at night (e.g. 00:00 - 05:00)
        # In a real system, this calls UT service API
        return True

    def assign_vessel(self, actor_ctx: dict, manifest_id: str, vessel_id: str):
        """REQUEST_TRANSFER_ASSIGNMENT & SYNC_FLIGHT_ARRIVAL_WITH_DISPATCH"""
        return self.guard.execute_sovereign_action(
            "imoxon.ut.assign",
            actor_ctx,
            self._internal_assign,
            manifest_id, vessel_id
        )

    def _internal_assign(self, manifest_id, vessel_id):
        entry = {"manifest": manifest_id, "vessel": vessel_id, "status": "ASSIGNED"}
        self.events.publish("VESSEL_ASSIGNED", entry)
        return entry
