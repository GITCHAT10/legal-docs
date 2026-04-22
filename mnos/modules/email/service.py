import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from mnos.core.security.aegis import aegis
from mnos.core.ai.silvia import silvia
from mnos.core.events.service import events
from mnos.modules.shadow.service import shadow

class EmailAuthority:
    """
    SKY-i EMAIL INTELLIGENCE: Secure mailbox management and ASI-driven processing.
    Adopting Perfex Mailbox concepts with Nextgen ASI logic.
    """
    def __init__(self):
        # Extend taxonomy for email events
        events.TAXONOMY.add("nexus.email.received")
        events.TAXONOMY.add("nexus.email.sent")
        # Ensure subscribers mapping has the new events
        if "nexus.email.received" not in events.subscribers:
             events.subscribers["nexus.email.received"] = []
        if "nexus.email.sent" not in events.subscribers:
             events.subscribers["nexus.email.sent"] = []

    def ingest_inbound_email(self, sender: str, subject: str, body: str, session_context: Dict[str, Any]):
        """Ingests email and routes through ASI pipeline."""
        trace_id = str(uuid.uuid4())

        try:
            # 1. AEGIS: Verify mailbox access
            aegis.validate_session(session_context)

            # 2. SILVIA: Intelligent classification and intent discovery
            # We wrap the email content for Silvia
            input_text = f"Subject: {subject}\nBody: {body}"
            analysis = silvia.process_request(input_text)

            # 3. ASI Smart Reply Generation
            smart_reply = self._generate_asi_reply(analysis)

            # 4. Commit to SHADOW
            shadow.commit("nexus.email.received", {
                "sender": sender,
                "subject": subject,
                "intent": analysis.get("intent"),
                "confidence": analysis.get("confidence"),
                "trace_id": trace_id
            })

            # 5. Emit Event for downstream workflows
            events.publish("nexus.email.received", {
                "sender": sender,
                "subject": subject,
                "body": body,
                "analysis": analysis,
                "smart_reply": smart_reply
            }, trace_id=trace_id)

            # 6. Auto-Trigger Workflows based on ASI intent
            if analysis["status"] == "EXECUTE":
                self._trigger_asi_workflow(analysis, sender, trace_id)

            return {"status": "SUCCESS", "trace_id": trace_id, "smart_reply": smart_reply}

        except Exception as e:
            print(f"[EMAIL] CRITICAL FAILURE: {str(e)}")
            # Fail closed is implicit via exception
            raise

    def _generate_asi_reply(self, analysis: Dict[str, Any]) -> str:
        """Generates a contextual reply using NEXUS DNA."""
        if analysis.get("status") == "ESCALATE":
            return "Thank you for your email. I have escalated this to SKY-i COMMAND for further assistance."

        return f"Hello, I have identified your request as {analysis.get('intent')}. {analysis.get('response')}"

    def _trigger_asi_workflow(self, analysis: Dict[str, Any], sender: str, trace_id: str):
        """Bridges email intent to operational workflows."""
        intent = analysis.get("intent")
        if intent == "booking.created":
            events.publish("nexus.booking.created", {"sender": sender, "source": "EMAIL"}, trace_id=trace_id)
        elif intent == "guest.arrival":
            events.publish("nexus.guest.arrival", {"sender": sender, "source": "EMAIL"}, trace_id=trace_id)
        elif intent == "emergency.triggered":
            events.publish("nexus.emergency.triggered", {"sender": sender, "source": "EMAIL"}, trace_id=trace_id)

email_authority = EmailAuthority()
