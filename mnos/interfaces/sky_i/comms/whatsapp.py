import uuid
from typing import Dict, Any
from mnos.core.security.aegis import aegis
from mnos.core.ai.silvia import silvia
from mnos.core.events.service import events

class WhatsAppInterface:
    """
    SKY-i COMMS: WhatsApp Intelligence Loop integration.
    Route: SKY-i COMMS → AEGIS → SILVIA → JULES
    """
    def receive_message(self, phone: str, text: str, session_context: Dict[str, Any]):
        trace_id = str(uuid.uuid4())

        try:
            # 1. AEGIS: Identity/Device binding
            aegis.validate_session(session_context)

            # 2. SILVIA: Intelligence & Retrieval
            decision = silvia.process_request(text)

            if decision["status"] == "ESCALATE":
                return self._escalate(trace_id, phone, decision["reason"])

            # 3. JULES (Workflows) via EVENTS
            intent = decision['intent']
            # Hardened Routing: Prevent double-prefixing of legal or nexus intents
            event_type = intent if intent.startswith("elegal.") or intent.startswith("nexus.") else f"nexus.{intent}"

            event_payload = events.publish(
                event_type=event_type,
                data={
                    "phone": phone,
                    "text": text,
                    "response": decision["response"]
                },
                trace_id=trace_id
            )

            return {
                "status": "PROCESSED",
                "trace_id": trace_id,
                "response": decision["response"]
            }

        except Exception as e:
            return self._escalate(trace_id, phone, str(e))

    def _escalate(self, trace_id: str, phone: str, reason: str):
        print(f"[COMMS] ESCALATION Trace: {trace_id} | Reason: {reason}")
        return {
            "status": "ESCALATED",
            "trace_id": trace_id,
            "reason": reason
        }

whatsapp = WhatsAppInterface()
