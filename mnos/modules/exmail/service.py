import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from mnos.core.asi.silvia import silvia
from mnos.core.events.service import events
from mnos.shared.execution_guard import guard

class ExMailAuthority:
    """
    ExMAIL SOVEREIGN INTELLIGENCE (HARDENED).
    Provides secure, audited, and intelligent email-to-workflow processing via Execution Guard.
    """
    def __init__(self):
        # Taxonomy for ExMAIL
        self.TAXONOMY = [
            "exmail.received",
            "exmail.sent",
            "exmail.task.created",
            "exmail.ticket.created"
        ]
        events.register_taxonomy(self.TAXONOMY)

    def ingest_inbound_exmail(self, sender: str, subject: str, body: str, session_context: Dict[str, Any]):
        """Ingests email into the ExMAIL ASI pipeline enforced by Execution Guard."""
        try:
            # Advisory Intelligence
            input_text = f"Subject: {subject}\nBody: {body}"
            analysis = silvia.process_request(input_text)
            sentiment = self._analyze_sentiment(body)
            smart_reply = self._generate_smart_reply(analysis, sentiment)

            def execute_exmail(payload):
                self._handle_asi_conversions(payload["analysis"], payload["sender"], session_context)
                return {"processed": True, "sentiment": payload["sentiment"]}

            # Execute via Sovereign Guard
            guard.execute_sovereign_action(
                action_type="exmail.received",
                payload={
                    "sender": sender,
                    "subject": subject,
                    "analysis": analysis,
                    "sentiment": sentiment,
                    "smart_reply": smart_reply
                },
                session_context=session_context,
                execution_logic=execute_exmail
            )

            return {
                "status": "SUCCESS",
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

    def _handle_asi_conversions(self, analysis: Dict[str, Any], sender: str, session_context: Dict[str, Any]):
        """Nextgen ASI: Automatically converts emails into actionable CRM entities via Guarded Execution."""
        intent = analysis.get("intent")

        # Scenario: Booking becomes a Task
        if intent == "booking.created":
            # For each sub-action in a nested chain, we need a fresh nonce if we re-verify.
            # But the doctrine says REALITY -> SIGNED EVENT -> GUARD.
            # In a nested conversion, we should probably bypass re-verification or use one-time sub-tokens.
            # For this prototype, we'll ensure sub-actions don't re-trigger AEGIS or we provide sub-nonces.

            sub_ctx = session_context.copy()
            sub_ctx["nonce"] = f"{session_context['nonce']}:task"
            from mnos.core.security.aegis import aegis
            sub_ctx["signature"] = aegis.sign_session(sub_ctx)

            guard.execute_sovereign_action(
                "exmail.task.created",
                {"type": "RESERVATION_PROC", "sender": sender},
                sub_ctx,
                lambda x: None
            )

            sub_ctx2 = session_context.copy()
            sub_ctx2["nonce"] = f"{session_context['nonce']}:booking"
            sub_ctx2["signature"] = aegis.sign_session(sub_ctx2)

            guard.execute_sovereign_action(
                "nexus.booking.created",
                {"sender": sender, "source": "ExMAIL"},
                sub_ctx2,
                lambda x: None
            )

        # Scenario: Emergency becomes a Ticket
        elif intent == "emergency.triggered":
            sub_ctx3 = session_context.copy()
            sub_ctx3["nonce"] = f"{session_context['nonce']}:ticket"
            from mnos.core.security.aegis import aegis
            sub_ctx3["signature"] = aegis.sign_session(sub_ctx3)

            guard.execute_sovereign_action(
                "exmail.ticket.created",
                {"severity": "CRITICAL", "sender": sender},
                sub_ctx3,
                lambda x: None
            )

            sub_ctx4 = session_context.copy()
            sub_ctx4["nonce"] = f"{session_context['nonce']}:sos"
            sub_ctx4["signature"] = aegis.sign_session(sub_ctx4)

            guard.execute_sovereign_action(
                "nexus.emergency.triggered",
                {"sender": sender, "source": "ExMAIL"},
                sub_ctx4,
                lambda x: None
            )

exmail_authority = ExMailAuthority()
