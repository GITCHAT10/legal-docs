class RoleDetectionAI:
    """
    Bubble OS Role Detection: Automatically classifies users based on economic behavior.
    """
    def __init__(self):
        self.rules = {
            "fish_sales": "FISHERMAN",
            "crop_sales": "FARMER",
            "food_bakery": "VENDOR",
            "government": "GOV_OFFICER"
        }

    def predict_role(self, user_id: str, behavior_signals: dict):
        # RoleScore = f(Transaction Type, Asset Class, Frequency)
        primary_role = "UNKNOWN"
        confidence = 0.0

        tx_type = behavior_signals.get("tx_type")
        freq = behavior_signals.get("frequency", 0)

        if tx_type in self.rules:
            primary_role = self.rules[tx_type]
            confidence = 0.85 if freq > 5 else 0.60

        return {
            "user_id": user_id,
            "primary_role": primary_role,
            "secondary_role": "VENDOR" if freq > 10 else None,
            "confidence": confidence,
            "adaptive_ui": f"DASHBOARD_{primary_role}"
        }
