import unittest
from mnos.modules.ontology.service import ontology
from mnos.shared.execution_guard import guard
from mnos.core.security.aegis import aegis
from mnos.modules.shadow.semantic import semantic_audit
import json
import hmac
import hashlib

class TestOntologyGovernance(unittest.TestCase):
    def setUp(self):
        self.ctx_payload = {"device_id": "MIG-CEO-ONTOLOGY-01"}
        from mnos.config import config
        sig = hmac.new(config.NEXGEN_SECRET.encode(), json.dumps(self.ctx_payload, sort_keys=True, separators=(',', ':')).encode(), hashlib.sha256).hexdigest()
        self.ctx = self.ctx_payload.copy()
        self.ctx["signature"] = sig

    def test_causal_paradox_hold(self):
        # 1. Paradox Injection
        evidence_a = 1 # Physical
        evidence_b = 2 # Financial
        paradox = ontology.check_consistency(evidence_a, evidence_b)
        self.assertEqual(paradox["status"], "HOLD")

        # 2. Guard Adjudication
        with patch("builtins.print") as mock_print:
            res = guard.execute_sovereign_action(
                "nexus.financial.invoice",
                paradox,
                self.ctx,
                lambda p: "OK"
            )
            self.assertEqual(res["status"], "HOLD")
            mock_print.assert_any_call("[ExecutionGuard] CAUSAL PARADOX DETECTED: CP2026. Requesting MIG ADJUDICATION.")

    def test_semantic_canonical_hash(self):
        # 3. Canonical Hash Check
        trace = {
            "trace_id": "T1",
            "decision": "HOLD",
            "evidence_refs": ["E1", "E2"],
            "policy_id": "P10",
            "timestamp": "2026-01-01T00:00:00Z",
            "extra": "ignore_me"
        }
        h1 = semantic_audit.compute_canonical_hash(trace)

        # Reorder and add fields
        trace_alt = {
            "timestamp": "2026-01-01T00:00:00Z",
            "trace_id": "T1",
            "decision": "HOLD",
            "extra_2": "ignore_too",
            "policy_id": "P10",
            "evidence_refs": ["E1", "E2"]
        }
        h2 = semantic_audit.compute_canonical_hash(trace_alt)

        self.assertEqual(h1, h2)

from unittest.mock import patch
if __name__ == "__main__":
    unittest.main()
