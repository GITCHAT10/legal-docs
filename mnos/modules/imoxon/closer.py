import uuid
import structlog
from typing import Dict, Any, Optional
from datetime import datetime, UTC

logger = structlog.get_logger("prestige.closer")

class CloserNegotiationEngine:
    """
    Closer Negotiation Engine: Human-in-the-loop pricing overrides.
    Integrated with SHADOW ledger for forensic audit.
    """
    def __init__(self, core):
        self.core = core

    def submit_override(self,
                        pricing_decision: Dict[str, Any],
                        new_price_mvr: float,
                        reason: str,
                        closer_id: str):
        """
        Human closer adjusts AI price -> signed -> logged.
        - Automated CEO approval if deviation <= 10%
        """
        original_price = float(pricing_decision.get("final_gross", 0))
        if original_price <= 0:
             raise ValueError("FAIL CLOSED: Invalid original price for override")

        deviation_pct = abs(original_price - new_price_mvr) / original_price

        override_event = {
            "original_decision_id": pricing_decision.get("pricing_id"),
            "original_trace_id": pricing_decision.get("trace_id"),
            "new_amount_mvr": new_price_mvr,
            "deviation_pct": round(deviation_pct, 4),
            "reason": reason,
            "closer_id": closer_id,
            "approved_by_ceo": deviation_pct <= 0.10,
            "status": "APPROVED" if deviation_pct <= 0.10 else "PENDING_CEO_APPROVAL",
            "timestamp": datetime.now(UTC).isoformat()
        }

        # COMMIT TO SHADOW
        return self.core.execute_commerce_action(
            "pricing.override.submitted",
            {"identity_id": closer_id, "role": "closer", "device_id": "STATION_PH_01"},
            self._internal_emit_override,
            override_event
        )

    def _internal_emit_override(self, data):
        # 1. Publish to Event Bus
        self.core.events.publish("pricing.override", data)

        # 2. Forensic Log for SHADOW (already handled by execute_commerce_action)
        logger.info("price_override_recorded",
                    closer_id=data["closer_id"],
                    approved=data["approved_by_ceo"],
                    deviation=data["deviation_pct"])

        return data
