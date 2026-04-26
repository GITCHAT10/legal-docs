import uuid
import hashlib
from datetime import datetime, UTC
from mnos.modules.finance.fce import FCEEngine

class CustomsPayConnector:
    """
    CustomsPay Connector Service (FastAPI Stub).
    Handles MIRA/Customs duty settlement via ILUVIA Wallet.
    """
    def __init__(self, fce: FCEEngine):
        self.fce = fce

    def settle_duty(self, actor_id: str, amount: float, declaration_id: str, supervisor_id: str = None) -> dict:
        # Rule: Two-Person Approval for high value (> 50,000 MVR)
        if amount > 50000 and not supervisor_id:
             return {
                 "status": "AWAITING_APPROVAL",
                 "declaration_id": declaration_id,
                 "message": "Two-person approval required for high-value duty settlement."
             }

        # 1. ILUVIA_OPS_WALLET_DEBIT_STUB
        # Simulate a successful wallet debit via FCE context
        # In production: self.fce.debit_wallet(actor_id, amount, "CUSTOMS_DUTY")

        # 2. MCS Receipt Hashing
        receipt_id = f"MCS-PAY-{uuid.uuid4().hex[:8].upper()}"
        receipt_hash = hashlib.sha256(f"{receipt_id}|{declaration_id}|{amount}".encode()).hexdigest()

        from mnos.db.session import SessionLocal
        from mnos.modules.imoxon.logistics.models import ClearanceDeclaration

        with SessionLocal() as db:
            dec = db.query(ClearanceDeclaration).filter(ClearanceDeclaration.declaration_id == declaration_id).first()
            if dec:
                dec.current_state = "PAID"
                history = list(dec.state_history)
                history.append({
                    "state": "PAID",
                    "ts": datetime.now(UTC).isoformat(),
                    "receipt_id": receipt_id,
                    "approved_by": supervisor_id if amount > 50000 else actor_id
                })
                dec.state_history = history
                db.commit()

        return {
            "status": "SUCCESS",
            "receipt_id": receipt_id,
            "receipt_hash": receipt_hash,
            "amount_paid": amount,
            "currency": "MVR",
            "timestamp": datetime.now(UTC).isoformat()
        }
