import uuid
from datetime import datetime, UTC
from typing import Dict, Any, Optional

class Normalizer:
    @staticmethod
    def to_unified(channel: str, raw_payload: dict):
        """Normalize various channel payloads into a unified message format."""
        return {
            'sender': raw_payload.get('sender', 'unknown'),
            'content': raw_payload.get('content', ''),
            'channel': channel,
            'timestamp': datetime.now(UTC).isoformat()
        }

class AIBrain:
    @staticmethod
    def classify(content: str, role: str):
        """Classify message intent, risk, and department."""
        content_lower = content.lower()
        risk = "GREEN"
        priority = "P3"
        intent = "GENERAL_INQUIRY"
        dept = "GUEST_SERVICES"

        if any(word in content_lower for word in ["help", "stranded", "emergency", "danger"]):
            risk = "RED"
            priority = "P1"
            intent = "EMERGENCY"
            dept = "SAFETY"
        elif any(word in content_lower for word in ["refund", "billing", "wrong"]):
            risk = "YELLOW"
            priority = "P2"
            intent = "BILLING_ISSUE"
            dept = "FINANCE"

        # Hardened rules for Sovereign context
        if role == "vip":
            priority = "P1"

        return {
            'risk': risk,
            'priority': priority,
            'intent': intent,
            'dept': dept
        }

class Conversation:
    def __init__(self, conv_id, identity_id, priority, messages):
        self.id = conv_id
        self.identity_id = identity_id
        self.last_activity_at = datetime.now(UTC)
        self.ai_action = "PENDING"
        self.escalation_state = "INIT"
        self.priority = priority
        self.messages = messages

    def to_dict(self):
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "priority": self.priority,
            "ai_action": self.ai_action,
            "escalation_state": self.escalation_state
        }

class ConversationGraph:
    _conversations = {}

    @classmethod
    def link_or_create(cls, msg, identity, classification):
        """Link message to existing conversation or create a new one."""
        # In a real system, we would look up by identity and recent activity
        conv_id = f"CONV-{uuid.uuid4().hex[:8].upper()}"
        conv = Conversation(
            conv_id=conv_id,
            identity_id=identity.get('identity_id'),
            priority=classification['priority'],
            messages=[msg]
        )
        cls._conversations[conv_id] = conv
        return conv

class EscalationTimer:
    _timers = {}

    @classmethod
    def start(cls, conv_id: str, priority: str):
        cls._timers[conv_id] = {
            "start_time": datetime.now(UTC),
            "priority": priority,
            "active": True
        }

class ExMailEngine:
    """
    ExMail Engine: Communication OS for MAC EOS.
    Handles ingestion, AI classification, and sovereign routing.
    """
    def __init__(self, aegis, shadow, event_bus):
        self.aegis = aegis
        self.shadow = shadow
        self.event_bus = event_bus

    def ingest(self, channel: str, raw_payload: dict):
        # 1. Normalize
        msg = Normalizer.to_unified(channel, raw_payload)

        # 2. Resolve Identity via AEGIS
        profile_id = self._resolve_identity(msg['sender'])
        profile = self.aegis.profiles.get(profile_id) if profile_id else {"profile_type": "guest"}
        identity = {"identity_id": profile_id or "ANON", "role": profile.get("profile_type", "guest")}

        # 3. AI Classification
        classification = AIBrain.classify(msg['content'], identity["role"])

        # 4. Conversation Management
        conv = ConversationGraph.link_or_create(msg, identity, classification)

        # 5. Traffic Light Control
        if classification['risk'] in ["RED", "BLACK"]:
            conv.ai_action = "LOCKED"
            EscalationTimer.start(conv.id, priority=classification['priority'])
        elif classification['risk'] == "YELLOW":
            conv.ai_action = "DRAFT_ONLY"
        else:
            conv.ai_action = "AUTO_SEND"

        # 6. Immutable Audit & Event Publication
        # NOTE: Called within ExecutionGuard context from main.py
        # These will succeed because ExecutionGuard.is_authorized() will be True
        self.shadow.commit("exmail.received", conv.id, {
            "channel": channel,
            "intent": classification['intent'],
            "risk": classification['risk'],
            "priority": classification['priority']
        })

        if self.event_bus:
            self.event_bus.publish(f"exmail.conv.{conv.id}", {
                "status": "routed",
                "dept": classification['dept'],
                "ai_action": conv.ai_action
            })

        return conv.to_dict()

    def _resolve_identity(self, identifier: str) -> Optional[str]:
        # Simple lookup across AEGIS profiles
        for pid, p in self.aegis.profiles.items():
            if p.get("external_ref") == identifier or p.get("full_name") == identifier:
                return pid
        return None
