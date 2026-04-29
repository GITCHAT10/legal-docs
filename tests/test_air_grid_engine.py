import unittest
from datetime import datetime, UTC, time
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.modules.imoxon.policies.engine import IdentityPolicyEngine
from mnos.modules.finance.fce import FCEEngine
from mnos.shared.execution_guard import ExecutionGuard
from mnos.modules.imoxon.core.engine import ImoxonCore
from mnos.modules.air_grid.engine import AirGridEngine

class TestAirGridEngine(unittest.TestCase):
    def setUp(self):
        self.shadow = ShadowLedger()
        self.events = DistributedEventBus()
        self.identity = AegisIdentityCore(self.shadow, self.events)
        self.policy = IdentityPolicyEngine(self.identity)
        self.fce = FCEEngine()
        self.guard = ExecutionGuard(self.identity, self.policy, self.fce, self.shadow, self.events)
        self.imoxon = ImoxonCore(self.guard, self.fce, self.shadow, self.events)
        self.engine = AirGridEngine(self.imoxon)

        # Setup Ops Lead
        with self.guard.sovereign_context():
            self.ops_id = self.identity.create_profile({"full_name": "Ops Lead", "profile_type": "ops_lead"})
            self.ops_dev = self.identity.bind_device(self.ops_id, {"fingerprint": "OPS-DEV"})

        self.ops_ctx = {"identity_id": self.ops_id, "device_id": self.ops_dev, "role": "ops_lead"}

    def test_flight_ingestion_and_window_matching(self):
        flight_data = {
            "flight_id": "6E-141",
            "corridor": "INDIA_SOUTH",
            "scheduled_arrival": "2026-05-01T10:00:00Z",
            "estimated_arrival": "2026-05-01T10:15:00Z",
            "pax_count": 50
        }
        flight = self.engine.ingest_flight_update(self.ops_ctx, flight_data)

        self.assertEqual(flight["flight_id"], "6E-141")
        self.assertEqual(flight["delay_minutes"], 15.0)
        self.assertEqual(flight["window"], "W-MORNING-1")

    def test_transfer_assignment_with_revenue_pulse(self):
        # Ingest flight
        flight_data = {
            "flight_id": "FZ-567",
            "corridor": "GCC_DXB",
            "scheduled_arrival": "2026-05-01T21:00:00Z",
            "estimated_arrival": "2026-05-01T21:20:00Z", # 20min delay -> urgency premium
            "pax_count": 20
        }
        self.engine.ingest_flight_update(self.ops_ctx, flight_data)

        # Assign Transfer
        assignment = self.engine.assign_transfer(self.ops_ctx, "FZ-567")

        self.assertEqual(assignment["transfer_mode"], "seaplane")
        # GCC Base (1.15) + Urgency (0.05) = 1.20
        self.assertEqual(assignment["multiplier"], 1.20)
        self.assertEqual(assignment["status"], "ASSIGNED")

    def test_rbac_denial_for_standard_user(self):
        with self.guard.sovereign_context():
            user_id = self.identity.create_profile({"full_name": "Standard User", "profile_type": "user"})
            user_dev = self.identity.bind_device(user_id, {"fingerprint": "USER-DEV"})

        user_ctx = {"identity_id": user_id, "device_id": user_dev, "role": "user"}

        with self.assertRaises(PermissionError) as cm:
            self.engine.ingest_flight_update(user_ctx, {"flight_id": "FAIL-1"})
        self.assertIn("requires Air Grid write access", str(cm.exception))

if __name__ == "__main__":
    unittest.main()
