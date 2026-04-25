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
        import threading
        t = threading.current_thread()
        prev_flag = getattr(t, 'sovereign_guard', False)
        t.sovereign_guard = True
        token = in_sovereign_context.set(True)
        try:
            shadow.commit("nexus.guest.arrival", {"data": "valid"})
        finally:
            in_sovereign_context.reset(token)
            t.sovereign_guard = prev_flag

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

    def test_witness_mode_read_only(self):
        # 1. Enable witness mode
        shadow.enable_witness_mode()

        # 2. Attempt commit inside sovereign context
        import threading
        t = threading.current_thread()
        prev_flag = getattr(t, 'sovereign_guard', False)
        t.sovereign_guard = True
        token = in_sovereign_context.set(True)
        try:
            with self.assertRaises(RuntimeError) as cm:
                shadow.commit("nexus.guest.arrival", {"v": 1})
            self.assertIn("SHADOW_READ_ONLY", str(cm.exception))
        finally:
            in_sovereign_context.reset(token)
            t.sovereign_guard = prev_flag
            # Disable for other tests
            shadow.witness_mode = False

if __name__ == "__main__":
    unittest.main()
