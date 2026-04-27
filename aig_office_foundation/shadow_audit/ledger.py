from .hash_chain import HashChain
from .audit_events import create_audit_event

class ShadowLedger:
    """
    SHADOW Audit Ledger: Append-only immutable forensic trail.
    """
    def __init__(self):
        self.chain = HashChain()
        self.ledger = [] # List of {data, hash, prev_hash}

    def commit(self, event_type: str, actor_id: str, device_id: str, trace_id: str, payload: dict) -> str:
        if not trace_id:
             raise ValueError("SHADOW: trace_id is MANDATORY for all audit commits")

        event = create_audit_event(event_type, actor_id, device_id, trace_id, payload)
        prev_hash = self.chain.last_hash
        current_hash = self.chain.calculate_hash(event)

        block = {
            "data": event,
            "hash": current_hash,
            "prev_hash": prev_hash
        }

        self.ledger.append(block)
        self.chain.update(current_hash)

        return current_hash

    def verify_integrity(self) -> bool:
        temp_chain = HashChain()
        for block in self.ledger:
            if block["prev_hash"] != temp_chain.last_hash:
                return False
            calculated = temp_chain.calculate_hash(block["data"])
            if calculated != block["hash"]:
                return False
            temp_chain.update(calculated)
        return True
