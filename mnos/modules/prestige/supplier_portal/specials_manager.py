class SpecialsManager:
    def __init__(self, shadow):
        self.shadow = shadow
    def submit_special(self, actor_ctx, payload):
        self.shadow.commit("prestige.supplier.special_submitted", actor_ctx["identity_id"], payload)
        return {"status": "SPECIAL_SUBMITTED"}
