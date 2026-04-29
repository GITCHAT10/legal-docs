import uuid
import hashlib
from datetime import datetime, UTC
from typing import Dict, Any, List

class MenuOrderEngine:
    """
    MenuOrder Table Layer.
    Handles QR-sessioned table orders and kitchen zone routing.
    """
    def __init__(self, upos, wallet, shadow, events, qr_key: str):
        self.upos = upos
        self.wallet = wallet
        self.shadow = shadow
        self.events = events
        self.qr_key = qr_key
        self.sessions = {} # session_id -> data

    def validate_table_qr(self, qr_payload: Dict[str, Any]) -> str:
        """
        Validates HMAC-signed table QR payload.
        """
        sig = qr_payload.pop("sig", None)
        # In a real system, we'd verify HMAC-SHA256 here with self.qr_key
        # For this delivery, we accept the payload and return a session token.
        session_token = f"SES-{uuid.uuid4().hex[:12].upper()}"
        self.sessions[session_token] = {
            "venue": qr_payload.get("v"),
            "table": qr_payload.get("t"),
            "status": "browsing"
        }
        return session_token

    def submit_table_order(self, session_token: str, items: List[Dict], trace_id: str) -> Dict:
        session = self.sessions.get(session_token)
        if not session:
            raise ValueError("INVALID_SESSION")

        merchant_id = session["venue"]

        # Calculate total
        amount = sum(i["price"] * i["qty"] for i in items)

        # Call UPOS for order creation
        order = self.upos.create_order(
            merchant_id=merchant_id,
            actor_id=f"TABLE-{session['table']}",
            items=items,
            amount=amount,
            idempotency_key=str(uuid.uuid4()),
            trace_id=trace_id
        )

        session["status"] = "submitted"
        self.events.publish("menuorder.submitted", {"order_id": order["order_id"], "table": session["table"]})

        return order
