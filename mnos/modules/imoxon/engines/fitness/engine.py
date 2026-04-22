class FitnessEngine:
    """
    Deduplicated: Gym Master (Ops) + PreFit (User Experience).
    """
    def __init__(self, shadow, events):
        self.shadow = shadow
        self.events = events

    def register_membership(self, user_id: str, gym_id: str, plan: str):
        membership = {
            "user_id": user_id,
            "gym_id": gym_id,
            "plan": plan,
            "status": "ACTIVE"
        }
        self.shadow.record_action("fitness.membership", membership)
        self.events.trigger("MEMBERSHIP_STARTED", membership)
        return membership

    def log_workout(self, user_id: str, workout_details: dict):
        # PreFit mobile experience logic
        self.shadow.record_action("fitness.workout", {"user": user_id, **workout_details})
