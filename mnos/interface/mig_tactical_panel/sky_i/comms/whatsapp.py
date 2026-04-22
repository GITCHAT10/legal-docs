import uuid
from typing import Dict, Any
from mnos.core.ai.silvia import silvia
from mnos.shared.execution_guard import guard

class WhatsAppInterface:
    """
    SKY-i COMMS (HARDENED): WhatsApp Intelligence Loop.
    Route: SKY-i COMMS → AIGAegis → SILVIA → JULES
    Enforced via Execution Guard.
    """
    def receive_message(self, phone: str, text: str, session_context: Dict[str, Any], connection_context: Dict[str, Any] = None):
        try:
            # Default connection context for mobile gateways if not provided
            if connection_context is None:
                connection_context = {
                    "is_vpn": True,
                    "tunnel_id": "mobile-gateway-01",
                    "encryption": "wireguard",
                    "tunnel": "aig_tunnel",
                    "source_ip": "10.0.0.50",
                    "node_id": "COMMS-EDGE-01"
                }

            # Intelligence is advisory
            decision = silvia.process_request(text)
            if decision["status"] == "ESCALATE":
                return self._escalate("INTEL-ESC", phone, decision["reason"])

            def execute_workflow(payload):
                return {"response": payload["response"], "phone": payload["phone"]}

            # Execute via Sovereign Guard
            res = guard.execute_sovereign_action(
                action_type=f"nexus.{decision['intent']}",
                payload={
                    "phone": phone,
                    "text": text,
                    "response": decision["response"]
                },
                session_context=session_context,
                execution_logic=execute_workflow,
                connection_context=connection_context
            )

            return {
                "status": "PROCESSED",
                "response": res["response"]
            }

        except Exception as e:
            return self._escalate("GUARD-ESC", phone, str(e))

    def _escalate(self, trace_id: str, phone: str, reason: str):
        print(f"[COMMS] ESCALATION Trace: {trace_id} | Reason: {reason}")
        return {
            "status": "ESCALATED",
            "trace_id": trace_id,
            "reason": reason
        }

whatsapp = WhatsAppInterface()
