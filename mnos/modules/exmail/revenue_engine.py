import uuid
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
from decimal import Decimal

class MarketSegment(str, Enum):
    RUSSIA = "RUSSIA"
    GCC = "GCC"
    INDIA = "INDIA"
    EU = "EU"
    CHINA = "CHINA"
    SEA = "SEA"
    B2B = "B2B"
    B2C = "B2C"
    VIP = "VIP"

class TriggerType(str, Enum):
    PRICE_DROP = "price_drop"
    LOW_INVENTORY = "low_inventory"
    ABANDONED_BOOKING = "abandoned_booking"
    BOOKING_CREATED = "booking_created"
    PRE_CHECKIN = "pre_checkin"
    POST_CHECKOUT = "post_checkout"
    FLIGHT_LANDED = "flight_landed"

class AIRevenueHelper:
    """AI Layer for ROS: Generates subject lines and tunes offers."""

    @staticmethod
    def generate_subject(segment: MarketSegment, trigger: TriggerType, urgency: str = "medium") -> str:
        subjects = {
            TriggerType.PRICE_DROP: {
                MarketSegment.GCC: "Exclusive GCC Offer: Luxury Villa Price Drop 💎",
                MarketSegment.INDIA: "Limited Time: Special Discount for Your Maldives Trip 🌴",
                "DEFAULT": "Price Drop Alert: Your Dream Villa is Now More Accessible"
            },
            TriggerType.LOW_INVENTORY: {
                MarketSegment.RUSSIA: "⚠️ Последние 2 виллы на ваши даты!",
                "DEFAULT": "Hurry! Only a few rooms left for your dates"
            },
            TriggerType.ABANDONED_BOOKING: {
                MarketSegment.CHINA: "您的马尔代夫行程已保存 - 立即完成预订 ⚡",
                "DEFAULT": "Still thinking about your Maldives escape?"
            }
        }

        trigger_set = subjects.get(trigger, {})
        return trigger_set.get(segment, trigger_set.get("DEFAULT", f"Prestige Holidays: {trigger.value.replace('_', ' ').title()}"))

    @staticmethod
    def classify_segment(user_ctx: dict) -> MarketSegment:
        # Geographic + behavior logic
        geo = user_ctx.get("geo", "EU")
        if geo == "RU": return MarketSegment.RUSSIA
        if geo == "AE" or geo == "SA": return MarketSegment.GCC
        if geo == "IN": return MarketSegment.INDIA
        if geo == "CN": return MarketSegment.CHINA
        if geo == "SG" or geo == "TH": return MarketSegment.SEA
        return MarketSegment.EU

class CRMLABManager:
    """Mock interface for CRMLAB contacts and segment data."""
    def __init__(self):
        self.contacts = {
            "agent_1": {"email": "agent1@partner.com", "tier": "A", "geo": "RU"},
            "guest_1": {"email": "guest1@direct.com", "geo": "AE"}
        }

    def get_contact_data(self, identity_id: str) -> dict:
        return self.contacts.get(identity_id, {"email": "unknown@example.com", "geo": "EU"})

class EmailRevenueEngine:
    """
    Sovereign Email Revenue Engine (ROS): Transforms events into revenue opportunities.
    Integrated with PricingEngine and SHADOW ledger.
    """
    def __init__(self, core, pricing):
        self.core = core
        self.pricing = pricing
        self.crm = CRMLABManager()
        self.sent_log = []

    def handle_event(self, event_type: str, payload: dict):
        """Standard MNOS event handler."""
        # Convert internal events to TriggerType
        mapping = {
            "booking.created": TriggerType.BOOKING_CREATED,
            "flight.landed": TriggerType.FLIGHT_LANDED,
            "inventory.low": TriggerType.LOW_INVENTORY,
            "price.drop": TriggerType.PRICE_DROP,
            "booking.abandoned": TriggerType.ABANDONED_BOOKING,
            "pre.checkin": TriggerType.PRE_CHECKIN,
            "post.checkout": TriggerType.POST_CHECKOUT
        }

        trigger = mapping.get(event_type)
        if trigger:
            if trigger == TriggerType.ABANDONED_BOOKING:
                return self._start_recovery_sequence(payload)
            return self.process_trigger(trigger, payload)
        return None

    def _start_recovery_sequence(self, payload: dict):
        """Abandoned Booking Recovery Flow (High ROI)."""
        trace_id = payload.get("trace_id", str(uuid.uuid4()))

        # Immediate Reminder
        email1 = self.process_trigger(TriggerType.ABANDONED_BOOKING, payload)

        # Schedule next steps (Simulated)
        # T+6 hrs: Incentive email (Small discount)
        # T+24 hrs: Urgency push
        return {
            "status": "RECOVERY_INITIATED",
            "initial_email": email1,
            "trace_id": trace_id
        }

    def process_trigger(self, trigger: TriggerType, user_ctx: dict):
        # 1. Classify
        segment = AIRevenueHelper.classify_segment(user_ctx)

        # 2. Generate Subject (AI)
        subject = AIRevenueHelper.generate_subject(segment, trigger)

        # 3. Generate Deal (Dynamic Pricing)
        deal = self._generate_dynamic_deal(segment, trigger, user_ctx)

        # 4. Build & Dispatch
        return self._send_revenue_email(subject, deal, user_ctx, segment, trigger)

    def _generate_dynamic_deal(self, segment: MarketSegment, trigger: TriggerType, user_ctx: dict) -> dict:
        """Connects to PricingEngine to build a segment-weighted offer."""
        trace_id = user_ctx.get("trace_id", str(uuid.uuid4()))

        # Default amounts for ROS offers
        base_net = Decimal(str(user_ctx.get("preferred_price", "500.00")))

        # Channel rules: SOVEREIGN gives -5% disc
        channel = "SOVEREIGN"

        # Agent Tier Logic (B2B Core)
        agent_tier = user_ctx.get("agent_tier", "B") # A, B, C

        # B2B Strategic Adjustment
        agent_type = "B2B"
        allotment_override = None
        if agent_tier == "A":
            # Tier A agents get better pricing/priority
            allotment_override = Decimal("-0.05") # 5% lower cost
        elif agent_tier == "C":
            # Tactical push
            allotment_override = Decimal("0.05") # 5% higher cost for high demand

        return self.pricing.calculate_quote(
            net_amount=base_net,
            currency=user_ctx.get("currency", "USD"),
            product_type="PACKAGE",
            trace_id=trace_id,
            channel=channel,
            agent_type=agent_type,
            allotment_override_pct=allotment_override
        )

    def _send_revenue_email(self, subject: str, deal: dict, user_ctx: dict, segment: MarketSegment, trigger: TriggerType):
        email_id = f"REV-{uuid.uuid4().hex[:8].upper()}"
        trace_id = deal["breakdown"]["trace_id"]

        email_payload = {
            "email_id": email_id,
            "recipient": user_ctx.get("email"),
            "subject": subject,
            "segment": segment.value,
            "trigger": trigger.value,
            "offer": deal["breakdown"], # Full breakdown included (net, margin, commission, tax)
            "trace_id": trace_id,
            "status": "SENT",
            "timestamp": datetime.now(UTC).isoformat()
        }

        # COMMIT TO SHADOW via Core
        self.core.execute_commerce_action(
            "exmail.revenue_offer.sent",
            {"identity_id": "SYSTEM", "device_id": "SYSTEM_VIRTUAL", "role": "admin"},
            self._internal_log_and_publish,
            email_payload
        )

        return email_payload

    def _internal_log_and_publish(self, email_payload: dict):
        self.sent_log.append(email_payload)
        self.core.events.publish("exmail.revenue_offer_sent", email_payload)
        return email_payload
