import unittest
from mnos.core.monitor.service import risk_monitor
from mnos.shared.execution_guard import guard
from mnos.core.security.aegis import aegis
import json
import hmac
import hashlib

class TestRiskMonitor(unittest.TestCase):
    def setUp(self):
        self.ctx_payload = {"device_id": "MIG-MONITOR-CORE-2026"}
        from mnos.config import config
        sig = hmac.new(config.NEXGEN_SECRET.encode(), json.dumps(self.ctx_payload, sort_keys=True, separators=(',', ':')).encode(), hashlib.sha256).hexdigest()
        self.ctx = self.ctx_payload.copy()
        self.ctx["signature"] = sig

    def test_risk_evaluation_correlation(self):
        # 1. Ingest
        w_data = risk_monitor.ingest_data("weather", {"storm": True})
        self.assertEqual(w_data["source"], "weather")

        # 2. Evaluate
        risk = risk_monitor.evaluate_risk([w_data])
        self.assertGreater(risk["risk_score"], 0)
        self.assertIn("reasoning", risk)

    def test_execution_guard_advisory_mode(self):
        # 3. Guarded Advisory
        payload = {"risk_data": {"score": 0.8}}
        res = guard.execute_sovereign_action(
            "risk_monitor.alert",
            payload,
            self.ctx,
            lambda p: p
        )
        self.assertTrue(res["advisory_only"])
        self.assertTrue(res["human_decision_required"])

if __name__ == "__main__":
    unittest.main()
