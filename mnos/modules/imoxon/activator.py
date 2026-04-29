import uuid
import structlog
from typing import Dict, Any, List

logger = structlog.get_logger("prestige.activator")

class RevenueActivator:
    """
    Prestige Revenue Activator: Targets high-intent agents and dispatches offers.
    Integrated with MNOS Event Bus and ExecutionGuard.
    """
    def __init__(self, core):
        self.core = core
        self.dispatch_log = []

    def handle_pricing_event(self, event: Dict[str, Any]):
        """Consumes pricing.generated events."""
        decision = event["payload"]
        if self._should_activate(decision):
            self._dispatch_offer(decision)
            self._log_activation(decision)

    def _should_activate(self, decision: Dict[str, Any]) -> bool:
        """
        Targeting Logic:
        - Conversion probability > 0.75
        - Agent score > 0.82
        - Valid activation strategy
        """
        # Mocking extraction from decision/payload for targeting
        # In prod, these would be enriched fields in the PricingResponse context
        context = decision.get("request", {}).get("context", {})

        # Simulated enrichment for the demo/simulation
        conversion_prob = context.get("conversion_probability", 0.85)
        agent_score = context.get("agent_score", 0.90)
        strategy = context.get("strategy", "AGENT_TIER_OPTIMIZED")

        allowed_strategies = ["AGENT_TIER_OPTIMIZED", "JET_CHARTER_BUNDLE", "DYNAMIC_DEMAND_BASED"]

        return (conversion_prob > 0.75 and
                agent_score > 0.82 and
                strategy in allowed_strategies)

    def _dispatch_offer(self, decision: Dict[str, Any]):
        """Simulates multi-channel dispatch (WhatsApp/Email)."""
        agent_id = decision.get("request", {}).get("context", {}).get("agent_id", "UNKNOWN_AGENT")
        amount = float(decision.get("final_gross", 0))
        trace_id = decision.get("trace_id")

        offer_text = (
            f"🏝️ PRESTIGE EXCLUSIVE OFFER\n"
            f"Agent: {agent_id}\n"
            f"Price: {amount:,.2f} MVR\n"
            f"Valid: 48h | Book via portal or reply YES"
        )

        # Simulation: In prod, this calls external APIs
        channel = "WHATSAPP" if agent_id.startswith("WA_") else "EMAIL"
        logger.info("offer_dispatched", agent_id=agent_id, channel=channel, trace_id=trace_id)

        self.dispatch_log.append({
            "agent_id": agent_id,
            "channel": channel,
            "trace_id": trace_id,
            "status": "SENT"
        })

    def _log_activation(self, decision: Dict[str, Any]):
        """Emits AgentInteraction event via MNOS Core."""
        agent_id = decision.get("request", {}).get("context", {}).get("agent_id", "UNKNOWN_AGENT")
        interaction = {
            "agent_id": agent_id,
            "decision_id": decision.get("pricing_id"),
            "trace_id": decision.get("trace_id"),
            "interaction_type": "OUTREACH_SENT",
            "timestamp": decision.get("timestamp")
        }

        # Publish interaction event
        self.core.execute_commerce_action(
            "agent.interaction.recorded",
            {"identity_id": "SYSTEM", "role": "admin", "device_id": "SYSTEM_VIRTUAL"},
            self._internal_emit_interaction,
            interaction
        )

    def _internal_emit_interaction(self, data):
        self.core.events.publish("agent.interaction", data)
        return data
