class ShadowAdapter:
    def __init__(self, ledger):
        self.ledger = ledger

    def record_action(self, action_type: str, data: dict):
        # Immutable record via SHADOW
        return self.ledger.commit(f"imoxon.{action_type}", data)

    def verify_chain(self):
        return self.ledger.verify_integrity()
