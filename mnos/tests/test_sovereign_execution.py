import unittest
from mnos.core.events.service import events
from mnos.shared.execution_guard import guard
from mnos.modules.shadow.service import shadow
from mnos.core.security.aegis import aegis
import json

class TestSovereignExecution(unittest.TestCase):
    def setUp(self):
        shadow.chain = shadow.chain[:1]
        self.ctx_payload = {"device_id": "nexus-admin-01"}
        self.ctx = self.ctx_payload.copy()
        self.ctx["signature"] = aegis.sign_context(self.ctx_payload)

    def test_direct_publish_blocked(self):
        # Direct publish outside sovereign context MUST fail
        with self.assertRaises(RuntimeError) as cm:
            events.publish("nexus.booking.created", {"data": "direct"})
        self.assertIn("Write attempted outside Execution Guard", str(cm.exception))

    def test_guarded_publish_accepted(self):
        # Guarded execution inside sovereign context MUST succeed
        res = guard.execute_sovereign_action(
            "nexus.booking.created",
            {"data": "guarded"},
            self.ctx,
            lambda p: "done"
        )
        self.assertEqual(res, "done")
        self.assertTrue(shadow.verify_integrity())

if __name__ == "__main__":
    unittest.main()
