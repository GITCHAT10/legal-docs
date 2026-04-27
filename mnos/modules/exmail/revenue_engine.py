import uuid
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional
from enum import Enum
from decimal import Decimal

class MarketSegment(str, Enum):
    RUSSIA_CIS = "RUSSIA_CIS"
    GCC = "GCC"
    INDIA = "INDIA"
    CHINA = "CHINA"
    EU_UK = "EU_UK"
    SEA = "SEA"
    B2B = "B2B"
    B2C = "B2C"
    VIP = "VIP"
    REPEAT_GUEST = "REPEAT_GUEST"

class EmailRevenueEngine:
    """
    Sovereign Email Revenue Engine (ROS): Maps events to revenue opportunities.
    Integrated with PricingEngine for dynamic offer generation.
    """
    def __init__(self, core, pricing):
        self.core = core
        self.pricing = pricing
        self.sent_log = []

    def handle_event(self, event_type: str, payload: dict):
        """
        Triggers revenue-driven communication based on MNOS events.
        """
        # 1. Map event to trigger
        trigger_map = {
            "booking.created": self._trigger_upsell,
            "flight.landed": self._trigger_welcome_upsell,
            "payment.received": self._trigger_activity_gap_check,
            "stay.day2": self._trigger_spa_offer
        }

        handler = trigger_map.get(event_type)
        if handler:
            return handler(payload)
        return None

    def _trigger_upsell(self, payload: dict):
        # Generate dynamic offer for room upgrade
        trace_id = payload.get("trace_id", str(uuid.uuid4()))

        # Example: 20% discount for direct upsell
        offer = self.pricing.calculate_quote(
            net_amount=Decimal("300.00"),
            currency="USD",
            product_type="ACCOMMODATION",
            trace_id=trace_id,
            channel="SOVEREIGN" # -5% disc
        )

        return self._send_revenue_email(
            recipient=payload.get("guest_email"),
            template="UPSELL_VILLA",
            segment=payload.get("segment", MarketSegment.B2C),
            offer_data=offer,
            trace_id=trace_id
        )

    def _trigger_welcome_upsell(self, payload: dict):
        trace_id = payload.get("trace_id", str(uuid.uuid4()))
        # Transfer/Activity offer on landing
        offer = self.pricing.calculate_quote(
            net_amount=Decimal("150.00"),
            currency="USD",
            product_type="TRANSFER_AIR",
            trace_id=trace_id,
            channel="DIRECT"
        )
        return self._send_revenue_email(
            recipient=payload.get("guest_email"),
            template="WELCOME_AIR_UPGRADE",
            segment=payload.get("segment", MarketSegment.B2C),
            offer_data=offer,
            trace_id=trace_id
        )

    def _trigger_activity_gap_check(self, payload: dict):
        # Implementation for checking empty slots in itinerary
        pass

    def _trigger_spa_offer(self, payload: dict):
        pass

    def _send_revenue_email(self, recipient: str, template: str, segment: str, offer_data: dict, trace_id: str):
        email_id = f"REV-{uuid.uuid4().hex[:8].upper()}"

        email_record = {
            "email_id": email_id,
            "recipient": recipient,
            "template": template,
            "segment": segment,
            "offer_summary": offer_data["breakdown"],
            "trace_id": trace_id,
            "status": "SENT",
            "timestamp": datetime.now(UTC).isoformat()
        }

        # 2. Log to SHADOW for Audit & Revenue Tracking
        self.core.execute_commerce_action(
            "exmail.revenue_offer.sent",
            {"identity_id": "SYSTEM", "device_id": "SYSTEM_VIRTUAL", "role": "admin"},
            self._internal_send_and_publish,
            email_record
        )

        return email_record

    def _internal_send_and_publish(self, email_record: dict):
        self.sent_log.append(email_record)
        self.core.events.publish("exmail.revenue_offer_sent", email_record)
