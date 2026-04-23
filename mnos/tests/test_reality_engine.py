import unittest
import time
from mnos.modules.chronos.event_store import chronos_store
from mnos.core.chronos.service import provable_replay
from mnos.shared.execution_guard import guard
from mnos.core.security.aegis import aegis
import json
import hmac
import hashlib

class TestRealityEngine(unittest.TestCase):
    def setUp(self):
        self.stream_id = "TEST-RECON-01"
        self.ctx_payload = {"device_id": "MIG-REALITY-VERIFIED-2026"}
        from mnos.config import config
        sig = hmac.new(config.NEXGEN_SECRET.encode(), json.dumps(self.ctx_payload, sort_keys=True, separators=(',', ':')).encode(), hashlib.sha256).hexdigest()
        self.ctx = self.ctx_payload.copy()
        self.ctx["signature"] = sig

    def test_replay_determinism(self):
        # 1. Record events
        t_start = time.time() * 1e9
        chronos_store.append(self.stream_id, "SIGHTING", {"target": "vessel", "id": 1})
        time.sleep(0.001)
        t_checkpoint = time.time() * 1e9
        chronos_store.append(self.stream_id, "SIGHTING", {"target": "person", "id": 2})

        # 2. Replay to checkpoint
        state_1 = provable_replay.compute_state_hash(
            provable_replay.verify_replay(self.stream_id, int(t_checkpoint), "") # Mock empty hash to get state
        )
        # Wait, verify_replay returns bool. Let's use replay_engine directly
        from mnos.modules.chronos.replay import replay_engine
        s1 = replay_engine.replay_to_time(self.stream_id, int(t_checkpoint))
        h1 = provable_replay.compute_state_hash(s1)

        # 3. Replay again (Repeatability)
        s2 = replay_engine.replay_to_time(self.stream_id, int(t_checkpoint))
        h2 = provable_replay.compute_state_hash(s2)

        self.assertEqual(h1, h2)
        self.assertEqual(s1["target"], "vessel")

    def test_risk_gated_isolation(self):
        # 4. Test Isolation on high risk
        payload = {"anomaly_score": 0.9, "intent_confidence": 0.5}
        res = guard.execute_sovereign_action(
            "nexus.action.test",
            payload,
            self.ctx,
            lambda p: "EXECUTED"
        )
        self.assertEqual(res["status"], "ISOLATED")

if __name__ == "__main__":
    unittest.main()
