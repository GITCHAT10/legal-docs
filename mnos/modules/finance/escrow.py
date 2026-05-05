import uuid

class EscrowFCETCore:
    """
    ESCROW_FCE_TRANSACTION_CORE (RC1-PRODUCTION-BRIDGE)
    Handles transaction locking and settlement release governed by FCE.
    """
    def __init__(self, fce, shadow):
        self.fce = fce
        self.shadow = shadow
        self.locks = {} # ref_id -> lock_data

    def lock_funds(self, actor_id: str, ref_id: str, amount: float):
        lock_id = f"LCK-{uuid.uuid4().hex[:6].upper()}"
        lock_data = {
            "lock_id": lock_id,
            "ref_id": ref_id,
            "amount": amount,
            "status": "LOCKED"
        }
        self.locks[ref_id] = lock_data
        self.shadow.commit("finance.escrow.lock", actor_id, lock_data)
        return lock_data

    def release_to_settlement(self, actor_id: str, ref_id: str):
        if ref_id not in self.locks:
             raise ValueError("Funds not locked for this reference")

        lock = self.locks[ref_id]
        lock["status"] = "RELEASED"

        settlement_data = {
            "ref_id": ref_id,
            "amount": lock["amount"],
            "status": "SETTLED"
        }
        self.shadow.commit("finance.escrow.release", actor_id, settlement_data)
        return settlement_data
