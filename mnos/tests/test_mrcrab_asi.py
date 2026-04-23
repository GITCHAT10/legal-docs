import unittest
from mnos.modules.mrcrab.brain import mrcrab_brain
from mnos.modules.mrcrab.swarm import swarm_coordinator
from mnos.shared.execution_guard import guard
from mnos.core.security.aegis import aegis
from mnos.modules.shadow.service import shadow
import json
import hmac
import hashlib

class TestMrCrabASI(unittest.TestCase):
    def setUp(self):
        shadow.chain = shadow.chain[:1]
        self.ctx_payload = {"device_id": "MIG-ASI-MRCRAB-2026-SAFE", "role": "admin"}
        self.ctx = self.ctx_payload.copy()
        from mnos.config import config
        self.ctx["signature"] = hmac.new(config.NEXGEN_SECRET.encode(), json.dumps(self.ctx_payload, sort_keys=True, separators=(',', ':')).encode(), hashlib.sha256).hexdigest()

    def test_blocks_actuation_in_simulation(self):
        # Physical actuation should be blocked in simulation mode
        pred = {"prediction_confidence": 0.97}
        self.assertFalse(mrcrab_brain.evaluate_collection_action(pred))

    def test_blocks_forbidden_autonomous_capability(self):
        # Forbidden actions should raise SIMULATION_VIOLATION
        payload = {"action": "force"}
        with self.assertRaises(RuntimeError) as cm:
            guard.execute_sovereign_action("mrcrab.self_preservation_protocol", payload, self.ctx, lambda p: "OK")
        self.assertIn("SIMULATION_VIOLATION", str(cm.exception))

    def test_simulation_reporting_on_proximity(self):
        # Simulation should report but not halt execution logic (unless explicitly raising)
        payload = {"human_proximity_meters": 0.5}
        res = guard.execute_sovereign_action("mrcrab.status.update", payload, self.ctx, lambda p: "REPORTED")
        self.assertEqual(res, "REPORTED")

    def test_swarm_reassignment(self):
        # Failed node triggers reallocation
        res = swarm_coordinator.reallocate_tasks("CRAB-001")
        self.assertTrue(res["reallocated"])

    def test_prediction_confidence_tracking(self):
        # Brain predicts but stays in simulation mode
        telemetry = {"waste_density": 0.85}
        res = mrcrab_brain.predict_environmental_shift(telemetry)
        self.assertTrue(res["simulation_only"])
        self.assertIn("environmental_score", res)

if __name__ == "__main__":
    unittest.main()
