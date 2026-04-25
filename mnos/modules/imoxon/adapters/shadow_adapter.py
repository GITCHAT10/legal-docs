class ShadowAdapter:
    def __init__(self, ledger):
        self.ledger = ledger

    def record_action(self, action_type: str, data: dict):
        # Immutable record via SHADOW
        # In this adapter context, we use the organization/operator ID as the actor_id if present
        actor_id = data.get("operator_id") or data.get("organization_id") or "SYSTEM"
        return self.ledger.commit(f"imoxon.{action_type}", actor_id, data)

    def verify_chain(self):
        return self.ledger.verify_integrity()
