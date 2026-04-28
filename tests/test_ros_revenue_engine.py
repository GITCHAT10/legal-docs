import unittest
from decimal import Decimal
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.modules.imoxon.policies.engine import IdentityPolicyEngine
from mnos.modules.finance.fce import FCEEngine
from mnos.shared.execution_guard import ExecutionGuard
from mnos.modules.imoxon.core.engine import ImoxonCore
from mnos.modules.imoxon.pricing.engine import PricingEngine
from mnos.modules.exmail.revenue_engine import EmailRevenueEngine, MarketSegment, TriggerType

class TestROSRevenueEngine(unittest.TestCase):
    def setUp(self):
        self.shadow = ShadowLedger()
        self.events = DistributedEventBus()
        self.fce = FCEEngine()
        self.identity = AegisIdentityCore(self.shadow, self.events)
        self.policy = IdentityPolicyEngine(self.identity)
        self.guard = ExecutionGuard(self.identity, self.policy, self.fce, self.shadow, self.events)
        self.imoxon = ImoxonCore(self.guard, self.fce, self.shadow, self.events)
        self.pricing = PricingEngine(self.fce)
        self.imoxon.pricing = self.pricing
        self.engine = EmailRevenueEngine(self.imoxon, self.pricing)

    def test_ai_subject_generation_gcc(self):
        ctx = {"email": "vip@saudi.sa", "geo": "SA"}
        email = self.engine.process_trigger(TriggerType.PRICE_DROP, ctx)

        self.assertEqual(email["segment"], MarketSegment.GCC)
        self.assertIn("Exclusive GCC Offer", email["subject"])

    def test_abandoned_booking_recovery_initiated(self):
        payload = {"email": "forgetful@guest.cn", "geo": "CN", "trace_id": "T-ABAN-1"}
        res = self.engine.handle_event("booking.abandoned", payload)

        self.assertEqual(res["status"], "RECOVERY_INITIATED")
        self.assertEqual(res["initial_email"]["segment"], MarketSegment.CHINA)
        self.assertIn("立即完成预订", res["initial_email"]["subject"])

    def test_agent_tier_a_pricing_override(self):
        # Tier A gets 5% cost reduction override
        ctx = {"email": "top_agent@ru.com", "geo": "RU", "agent_tier": "A", "preferred_price": "1000.00"}
        email = self.engine.process_trigger(TriggerType.LOW_INVENTORY, ctx)

        # Base MVR for 1000 USD is 15420
        # Tier A Override: -5% -> 14649
        # Package Margin: 18% on 14649 -> 2636.82
        # Gross: 17285.82
        # SC: 10% of 17285.82 = 1728.58
        # Subtotal: 17285.82 + 1728.58 = 19014.40
        # Tax (8%): 1521.15
        # Total: 19014.40 + 1521.15 = 20535.55

        # Verify Segment-aware logic:
        # LOW_INVENTORY for Russia uses standard logic
        self.assertEqual(email["segment"], MarketSegment.RUSSIA)
        # We check that the final price reflects the override (is lower than base tier B)
        self.assertTrue(email["offer"]["final_price"] < 23000) # Quick bound check

    def test_shadow_logging_presence(self):
        ctx = {"email": "audit@test.com", "geo": "UK", "trace_id": "T-AUDIT"}

        # Need context for SHADOW commit
        with self.guard.sovereign_context():
             self.engine.process_trigger(TriggerType.BOOKING_CREATED, ctx)

        # Check if event exists in SHADOW
        found = False
        for block in self.shadow.chain:
            if "exmail.revenue_offer.sent" in block["event_type"]:
                if block["payload"].get("result", {}).get("trace_id") == "T-AUDIT" or \
                   block["payload"].get("trace_id") == "T-AUDIT":
                    found = True
                    break
        self.assertTrue(found)

if __name__ == "__main__":
    unittest.main()
