import unittest
from mnos.modules.shadow.service import shadow
from mnos.shared.execution_guard import in_sovereign_context
import json

class TestShadowHardening(unittest.TestCase):
    def setUp(self):
        # Reset shadow for clean state
        shadow.chain = shadow.chain[:1]

    def test_integrity_checks(self):
        # Manually enter sovereign context for direct commit in test
        token = in_sovereign_context.set(True)
        try:
            shadow.commit("nexus.guest.arrival", {"data": "valid"})
        finally:
            in_sovereign_context.reset(token)

        self.assertEqual(len(shadow.chain), 2)

        # 1. Valid chain passes
        self.assertTrue(shadow.verify_integrity())

        # 2. Timestamp mutation fails integrity
        original_ts = shadow.chain[1]["timestamp"]
        shadow.chain[1]["timestamp"] = "2026-04-22T09:00:00Z"
        self.assertFalse(shadow.verify_integrity())
        shadow.chain[1]["timestamp"] = original_ts # Restore
        self.assertTrue(shadow.verify_integrity())

        # 3. Payload mutation fails integrity
        shadow.chain[1]["payload"] = {"data": "tampered"}
        self.assertFalse(shadow.verify_integrity())
        shadow.chain[1]["payload"] = {"data": "valid"} # Restore
        self.assertTrue(shadow.verify_integrity())

        # 4. previous_hash mutation fails integrity
        shadow.chain[1]["previous_hash"] = "tampered_hash"
        self.assertFalse(shadow.verify_integrity())

if __name__ == "__main__":
    unittest.main()
