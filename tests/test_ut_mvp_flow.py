import unittest
from datetime import datetime, UTC, timedelta
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.modules.imoxon.policies.engine import IdentityPolicyEngine
from mnos.modules.finance.fce import FCEEngine
from mnos.shared.execution_guard import ExecutionGuard
from mnos.modules.imoxon.core.engine import ImoxonCore
from mnos.modules.air_grid.engine import AirGridEngine
from mnos.modules.air_grid.ut_bridge import UTMVPBridge

class TestUTMVPFlow(unittest.TestCase):
    def setUp(self):
        self.shadow = ShadowLedger()
        self.events = DistributedEventBus()
        self.identity = AegisIdentityCore(self.shadow, self.events)
        self.policy = IdentityPolicyEngine(self.identity)
        self.fce = FCEEngine()
        self.guard = ExecutionGuard(self.identity, self.policy, self.fce, self.shadow, self.events)
        self.imoxon = ImoxonCore(self.guard, self.fce, self.shadow, self.events)
        self.bridge = UTMVPBridge(self.imoxon)
        self.engine = AirGridEngine(self.imoxon, ut_bridge=self.bridge)

        with self.guard.sovereign_context():
            self.ops_id = self.identity.create_profile({"full_name": "Ops Lead", "profile_type": "ops_lead"})
            self.ops_dev = self.identity.bind_device(self.ops_id, {"fingerprint": "OPS-DEV"})
        self.ops_ctx = {"identity_id": self.ops_id, "device_id": self.ops_dev, "role": "ops_lead"}

    def test_auto_reschedule_on_delay(self):
        # 1. Ingest flight with 40min delay
        flight_data = {
            "flight_id": "6E-141",
            "corridor": "INDIA_SOUTH",
            "scheduled_arrival": "2026-05-01T10:00:00Z",
            "estimated_arrival": "2026-05-01T10:40:00Z",
            "pax_count": 2,
            "ut_ticket_ref": "UT-001"
        }

        # This triggers bridge.attempt_auto_adjust internally
        self.engine.ingest_flight_update(self.ops_ctx, flight_data)

        # 2. Verify state (Simulated via capacity reduction)
        # 10 default - 2 pax = 8 remaining in the bucket
        # We check bucket creation logic
        arrival_plus_buffer = datetime.now(UTC) + timedelta(minutes=40+45)
        bucket = arrival_plus_buffer.replace(second=0, microsecond=0)
        self.assertEqual(self.bridge.capacity_cache[bucket], 8)

    def test_no_capacity_fallback_to_manual(self):
        # 1. Set capacity to low
        arrival_time = datetime.now(UTC) + timedelta(minutes=35+45)
        bucket = arrival_time.replace(second=0, microsecond=0)
        self.bridge.capacity_cache[bucket] = 1 # Only 1 slot

        # 2. Ingest flight with 5 pax
        flight_data = {
            "flight_id": "FZ-123",
            "corridor": "GCC_DXB",
            "scheduled_arrival": "2026-05-01T21:00:00Z",
            "estimated_arrival": "2026-05-01T21:35:00Z",
            "pax_count": 5,
            "ut_ticket_ref": "UT-002"
        }
        self.engine.ingest_flight_update(self.ops_ctx, flight_data)

        # 3. Check Manual Queue
        self.assertEqual(len(self.bridge.pending_adjustments), 1)
        adj = list(self.bridge.pending_adjustments.values())[0]
        self.assertEqual(adj["status"], "PENDING_MANUAL")
        self.assertEqual(adj["ut_ticket_ref"], "UT-002")

    def test_ops_lead_manual_approval(self):
        # 1. Setup manual adjustment
        adj_id = "MADJ-TEST"
        self.bridge.pending_adjustments[adj_id] = {
            "id": adj_id, "ut_ticket_ref": "UT-MAN", "status": "PENDING_MANUAL"
        }

        # 2. Approve
        res = self.bridge.process_manual_override(self.ops_ctx, adj_id, "approve")

        self.assertEqual(res["status"], "MANUAL_APPROVED")
        self.assertEqual(len(self.bridge.pending_adjustments), 0)

if __name__ == "__main__":
    unittest.main()
