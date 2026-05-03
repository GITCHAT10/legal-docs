import hashlib
from typing import Dict, Any
from mnos.modules.shadow.service import shadow

class MiraTgstMock:
    """
    MIRA TGST Integration (Mock): Idempotency key sha256(tin|period|shadow_hash).
    """
    def file_tgst_mock(self, tin: str, period: str, amount: float, shadow_hash: str) -> Dict[str, Any]:
        idempotency_input = f"{tin}|{period}|{shadow_hash}"
        idempotency_key = hashlib.sha256(idempotency_input.encode()).hexdigest()

        receipt = {
            "tin": tin,
            "period": period,
            "amount": amount,
            "idempotency_key": idempotency_key,
            "mira_receipt_no": f"MIRA-MOCK-{idempotency_key[:8].upper()}",
            "status": "SEALED_IN_SHADOW"
        }

        shadow.commit("elegal.mira.receipt_sealed", receipt)
        return receipt

mira_tgst = MiraTgstMock()
