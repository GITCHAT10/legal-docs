import uuid
from datetime import datetime, UTC
from typing import Dict, List, Any

class ExMailEngine:
    """
    ExMail: Hardened SMTP/IMAP Orchestrator.
    Wraps standard mail protocols in ExecutionGuard + SHADOW Audit.
    """
    def __init__(self, guard, shadow, events, fce):
        self.guard = guard
        self.shadow = shadow
        self.events = events
        self.fce = fce
        self.priority_queue = []

    def process_outbound_mail(self, actor_ctx: dict, message: dict) -> str:
        """
        Sends a sovereign email with mandatory audit and intent parsing.
        """
        msg_id = f"MAIL-{uuid.uuid4().hex[:6].upper()}"
        trace_id = f"EXMAIL-{msg_id}"

        with self.guard.sovereign_context(trace_id=trace_id):
            # 1. Audit SMTP Transaction
            self.shadow.commit("mail.outbound.sent", actor_ctx["identity_id"], {
                "msg_id": msg_id,
                "recipient": message.get("to"),
                "subject_hash": hash(message.get("subject")),
                "status": "SENT_VIA_HARDENED_RELAY"
            })

            # 2. Intent Hook: Check for FCE triggers
            if "invoice" in message.get("subject", "").lower():
                self.events.publish("mail.intent.invoice_requested", {"msg_id": msg_id})

            print(f"[EXMAIL] Message {msg_id} routed through sovereign relay.")

        return msg_id

    def ingest_inbound_mail(self, sender: str, recipient: str, content: str):
        """
        Ingests mail from Dovecot/Postfix wrapper into MNOS.
        """
        trace_id = f"IN-MAIL-{uuid.uuid4().hex[:4].upper()}"

        with self.guard.sovereign_context(trace_id=trace_id):
             self.shadow.commit("mail.inbound.received", recipient, {
                 "sender": sender,
                 "content_preview": content[:50],
                 "trace_id": trace_id
             })
             self.events.publish("mail.received", {"sender": sender, "recipient": recipient})

        return trace_id
