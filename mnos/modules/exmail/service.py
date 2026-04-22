import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from mnos.core.security.aegis import aegis
from mnos.core.ai.silvia import silvia
from mnos.core.events.service import events
from mnos.modules.shadow.service import shadow

class ExMailAuthority:
    """
    ExMAIL SOVEREIGN INTELLIGENCE: Adopted from Perfex Mailbox with Nextgen ASI.
    Provides secure, audited, and intelligent email-to-workflow processing.
    """
    def __init__(self):
        # Taxonomy for ExMAIL
        self.TAXONOMY = {
            "exmail.received",
            "exmail.sent",
            "exmail.task.created",
            "exmail.ticket.created"
        }
        for et in self.TAXONOMY:
            events.TAXONOMY.add(et)
            if et not in events.subscribers:
                events.subscribers[et] = []

    def ingest_inbound_exmail(self, sender: str, subject: str, body: str, session_context: Dict[str, Any]):
        """Ingests email into the ExMAIL ASI pipeline."""
        trace_id = str(uuid.uuid4())

        try:
            # 1. AEGIS Auth
            aegis.validate_session(session_context)

            # 2. SILVIA Intelligence
            input_text = f"Subject: {subject}\nBody: {body}"
            analysis = silvia.process_request(input_text)

            # 3. Nextgen ASI: Sentiment Analysis (Mocked)
            sentiment = self._analyze_sentiment(body)

            # 4. Smart Reply (NEXUS Context)
            smart_reply = self._generate_smart_reply(analysis, sentiment)

            # 5. SHADOW Commit
            shadow.commit("exmail.received", {
                "sender": sender,
                "subject": subject,
                "sentiment": sentiment,
                "intent": analysis.get("intent"),
                "trace_id": trace_id
            })

            # 6. Emit Core Events
            events.publish("exmail.received", {
                "sender": sender,
                "subject": subject,
                "analysis": analysis,
                "sentiment": sentiment,
                "smart_reply": smart_reply
            }, trace_id=trace_id)

            # 7. Nextgen Bridge: Conversion to Task/Ticket
            self._handle_asi_conversions(analysis, sender, trace_id)

            return {
                "status": "SUCCESS",
                "trace_id": trace_id,
                "sentiment": sentiment,
                "smart_reply": smart_reply
            }

        except Exception as e:
            print(f"[ExMAIL] CORE FAILURE: {str(e)}")
            raise

    def _analyze_sentiment(self, text: str) -> str:
        """ASI Sentiment Engine: Detects emotional tone of the email."""
        text_lower = text.lower()
        if any(word in text_lower for word in ["angry", "bad", "worst", "fail", "slow"]):
            return "NEGATIVE"
        if any(word in text_lower for word in ["happy", "good", "great", "thanks", "excellent"]):
            return "POSITIVE"
        return "NEUTRAL"

    def _generate_smart_reply(self, analysis: Dict[str, Any], sentiment: str) -> str:
        """Generates tone-aware smart replies using NEXUS DNA."""
        base_reply = f"Thank you for contacting NEXUS ASI. We have identified your intent as {analysis.get('intent')}."

        if sentiment == "NEGATIVE":
            return f"{base_reply} We apologize for any inconvenience and have prioritized your request for SKY-i COMMAND review."

        return f"{base_reply} {analysis.get('response')}"

    def _handle_asi_conversions(self, analysis: Dict[str, Any], sender: str, trace_id: str):
        """Nextgen ASI: Automatically converts emails into actionable CRM entities."""
        intent = analysis.get("intent")

        # Scenario: Booking becomes a Task
        if intent == "booking.created":
            events.publish("exmail.task.created", {"type": "RESERVATION_PROC", "sender": sender}, trace_id=trace_id)
            events.publish("nexus.booking.created", {"sender": sender, "source": "ExMAIL"}, trace_id=trace_id)

        # Scenario: Emergency becomes a Ticket
        elif intent == "emergency.triggered":
            events.publish("exmail.ticket.created", {"severity": "CRITICAL", "sender": sender}, trace_id=trace_id)
            events.publish("nexus.emergency.triggered", {"sender": sender, "source": "ExMAIL"}, trace_id=trace_id)

exmail_authority = ExMailAuthority()
