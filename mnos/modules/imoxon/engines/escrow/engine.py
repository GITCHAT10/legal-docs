class EscrowEngine:
    """
    IMOXON ESCROW: Secure holding and dispute management.
    """
    def __init__(self, shadow, events):
        self.shadow = shadow
        self.events = events
        self.escrows = {}

    def create_escrow(self, from_user: str, to_user: str, amount: float, conditions: list):
        escrow_id = f"esc_{hash(from_user + to_user + str(amount)) % 10000}"
        hold = {
            "id": escrow_id,
            "from": from_user,
            "to": to_user,
            "amount": amount,
            "conditions": conditions,
            "status": "LOCKED"
        }
        self.shadow.commit("escrow.locked", hold)
        self.events.publish("PAYMENT_AUTHORIZED", hold)
        self.escrows[escrow_id] = hold
        return hold

    def release_escrow(self, escrow_id: str, dispute: bool = False):
        if escrow_id not in self.escrows: return False
        status = "DISPUTED" if dispute else "RELEASED"
        self.escrows[escrow_id]["status"] = status
        self.shadow.commit("escrow.released", {"id": escrow_id, "status": status})
        self.events.publish("PAYMENT_CAPTURED", {"id": escrow_id})
        return True
