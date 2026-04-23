import unittest
from mnos.core.aether.service import aether_intel
from mnos.shared.execution_guard import guard
from mnos.core.security.aegis import aegis
import json
import hmac
import hashlib

class TestAetherIntelligence(unittest.TestCase):
    def setUp(self):
        self.ctx_payload = {"device_id": "MIG-AETHER-CIVIL-2026"}
        from mnos.config import config
        sig = hmac.new(config.NEXGEN_SECRET.encode(), json.dumps(self.ctx_payload, sort_keys=True, separators=(',', ':')).encode(), hashlib.sha256).hexdigest()
        self.ctx = self.ctx_payload.copy()
        self.ctx["signature"] = sig

    def test_space_risk_evaluation(self):
        # 1. Evaluate Risk
        telemetry = {"solar_flux": 250}
        risk = aether_intel.evaluate_space_risk(telemetry)
        self.assertEqual(risk["risk_level"], "HIGH (SOLAR_STORM_RISK)")
        self.assertEqual(risk["status"], "ADVISORY_ONLY")

    def test_execution_guard_aether_advisory(self):
        # 2. Guarded Advisory
        payload = {"risk_data": {"level": "HIGH"}}
        res = guard.execute_sovereign_action(
            "aether.space_risk.detected",
            payload,
            self.ctx,
            lambda p: p
        )
        self.assertTrue(res["advisory_only"])
        self.assertTrue(res["human_decision_required"])

if __name__ == "__main__":
    unittest.main()
