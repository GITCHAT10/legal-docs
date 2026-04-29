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
from mnos.modules.exmail.revenue_engine import EmailRevenueEngine

class TestEmailRevenueEngine(unittest.TestCase):
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

    def test_booking_created_trigger_upsell(self):
        event_payload = {
            "guest_email": "vip@example.com",
            "segment": "VIP",
            "trace_id": "T-BO-123"
        }

        # Manually trigger
        email = self.engine.handle_event("booking.created", event_payload)

        self.assertIsNotNone(email)
        self.assertEqual(email["template"], "UPSELL_VILLA")
        self.assertEqual(email["trace_id"], "T-BO-123")
        # Ensure price breakdown is attached
        self.assertIn("final_price", email["offer_summary"])

    def test_flight_landed_trigger_welcome(self):
        event_payload = {
            "guest_email": "guest@example.com",
            "trace_id": "T-FL-456"
        }
        email = self.engine.handle_event("flight.landed", event_payload)

        self.assertEqual(email["template"], "WELCOME_AIR_UPGRADE")
        self.assertEqual(email["offer_summary"]["margin_pct"], 0.08) # TRANSFER_AIR

if __name__ == "__main__":
    unittest.main()
