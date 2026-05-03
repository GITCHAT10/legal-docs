import hashlib
import uuid

class ConsentEngine:
    """
    MNOS Consent & Approval Engine.
    Manages multi-party approvals for design and construction milestones.
    """
    def __init__(self, shadow):
        self.shadow = shadow

    def request_approval(self, scope: str, actor_id: str, payload: dict) -> dict:
        approval_id = str(uuid.uuid4())
        approval_hash = hashlib.sha256(f"{scope}-{approval_id}".encode()).hexdigest()

        event = {
            "approval_id": approval_id,
            "scope": scope,
            "actor_id": actor_id,
            "payload": payload,
            "status": "PENDING",
            "approval_hash": approval_hash
        }

        self.shadow.commit(f"consent.request.{scope}", actor_id, event)
        return event

    def approve(self, approval_id: str, approver_id: str, scope: str) -> dict:
        result = {
            "approval_id": approval_id,
            "approver_id": approver_id,
            "approval_scope": scope,
            "approval_status": "APPROVED",
            "approval_hash": hashlib.sha256(f"APPROVED-{approval_id}".encode()).hexdigest()
        }
        self.shadow.commit(f"consent.approved.{scope}", approver_id, result)
        return result
