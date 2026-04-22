import unittest
from mnos.modules.shadow.service import shadow
from mnos.shared.execution_guard import guard
from mnos.shared.execution_guard import in_sovereign_context
import json

class TestShadowHardening(unittest.TestCase):
    def setUp(self):
        # Reset shadow for clean state
        shadow.chain = shadow.chain[:1]

    def test_timestamp_integrity(self):
        # Manually enter sovereign context for direct commit in test
        token = in_sovereign_context.set(True)
        try:
            shadow.commit("nexus.guest.arrival", {"data": "valid"})
        finally:
            in_sovereign_context.reset(token)

        self.assertEqual(len(shadow.chain), 2)

        # Verify integrity passes
        self.assertTrue(shadow.verify_integrity())

        # Tamper with the timestamp of the new entry
        shadow.chain[1]["timestamp"] = "2026-04-22T09:00:00Z"

        # Verify integrity fails
        self.assertFalse(shadow.verify_integrity())

if __name__ == "__main__":
    unittest.main()
