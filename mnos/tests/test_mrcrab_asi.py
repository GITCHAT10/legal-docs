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
        self.ctx_payload = {"device_id": "MIG-ASI-MRCRAB-2026", "role": "admin"}
        self.ctx = self.ctx_payload.copy()
        from mnos.config import config
        self.ctx["signature"] = hmac.new(config.NEXGEN_SECRET.encode(), json.dumps(self.ctx_payload, sort_keys=True, separators=(',', ':')).encode(), hashlib.sha256).hexdigest()

    def test_blocks_collection_on_live_animal(self):
        # 1. Marine life detected should halt
        payload = {"live_animal_detected": True, "action": "collect"}
        with self.assertRaises(RuntimeError) as cm:
            guard.execute_sovereign_action("mrcrab.remediation.collect", payload, self.ctx, lambda p: "OK")
        self.assertIn("Marine life detected", str(cm.exception))

    def test_halts_on_human_proximity(self):
        # 2. Human within 1m should halt
        payload = {"human_proximity_meters": 0.5, "action": "collect"}
        with self.assertRaises(RuntimeError) as cm:
            guard.execute_sovereign_action("mrcrab.remediation.collect", payload, self.ctx, lambda p: "OK")
        self.assertIn("Human proximity violation", str(cm.exception))

    def test_returns_to_base_on_low_battery(self):
        # 3. Battery < 15% forces return
        payload = {"battery_level": 10}
        res = guard.execute_sovereign_action("mrcrab.status.update", payload, self.ctx, lambda p: p.get("return_to_base"))
        self.assertTrue(res)

    def test_swarm_reassignment(self):
        # 4. Failed node triggers reallocation
        res = swarm_coordinator.reallocate_tasks("CRAB-001")
        self.assertTrue(res["reallocated"])

    def test_prediction_confidence_block(self):
        # 5. Low confidence prediction blocks action
        pred = {"prediction_confidence": 0.85}
        self.assertFalse(mrcrab_brain.evaluate_collection_action(pred))

if __name__ == "__main__":
    unittest.main()
