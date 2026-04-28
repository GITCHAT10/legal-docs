import unittest
from decimal import Decimal
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.modules.imoxon.policies.engine import IdentityPolicyEngine
from mnos.modules.finance.fce import FCEEngine
from mnos.shared.execution_guard import ExecutionGuard
from mnos.modules.imoxon.core.engine import ImoxonCore
from mnos.modules.imoxon.pricing.engine import PricingEngine, ProductType
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
        ctx = {"email": "vip@saudi.sa", "geo": "SA", "trace_id": "T-GCC"}
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
        ctx = {
            "email": "top_agent@ru.com",
            "geo": "RU",
            "agent_tier": "A",
            "preferred_price": "1000.00",
            "product_type": "PACKAGE"
        }
        email = self.engine.process_trigger(TriggerType.LOW_INVENTORY, ctx)

        # Verify Price Trace presence
        self.assertIn("pricing_trace", email)
        self.assertEqual(email["offer"]["trace_id"], email["trace_id"])

        # Base 1000 USD -> 15420 MVR.
        # SOVEREIGN Channel (-5%) -> 14649.00
        # Tier A Override (-5%) -> 13916.55
        self.assertEqual(email["offer"]["cost_price"], 13916.55)
        self.assertEqual(email["segment"], MarketSegment.RUSSIA_CIS)

    def test_product_to_tax_mapping_retail(self):
        ctx = {
            "email": "shopper@eu.com",
            "geo": "UK",
            "product_type": "RETAIL",
            "preferred_price": "100.00"
        }
        email = self.engine.process_trigger(TriggerType.PRICE_DROP, ctx)

        # Retail calculation:
        # 100 USD -> 1542 MVR.
        # SOVEREIGN Channel (-5%) -> 1464.90
        # Margin (Default 10%) -> 146.49 -> 1611.39 Gross
        # SC (10%) -> 161.14 -> 1772.53 Subtotal
        # Tax (8%) -> 141.80
        self.assertEqual(email["offer"]["tgst"], 141.8)

    def test_invalid_amount_rejection(self):
        ctx = {"email": "hacker@test.com", "preferred_price": "-100.00"}
        with self.assertRaises(ValueError) as cm:
            self.engine.process_trigger(TriggerType.PRICE_DROP, ctx)
        self.assertIn("Invalid pricing input", str(cm.exception))

    def test_shadow_logging_with_trace(self):
        ctx = {"email": "audit@test.com", "geo": "UK", "trace_id": "T-TRACE-ROS"}

        with self.guard.sovereign_context():
             self.engine.process_trigger(TriggerType.BOOKING_CREATED, ctx)

        found = False
        for block in self.shadow.chain:
            if "exmail.revenue_offer.sent" in block["event_type"]:
                if block["payload"].get("trace_id") == "T-TRACE-ROS" or \
                   (block["payload"].get("result") and block["payload"]["result"].get("trace_id") == "T-TRACE-ROS"):
                    found = True
                    break
        self.assertTrue(found)

if __name__ == "__main__":
    unittest.main()
