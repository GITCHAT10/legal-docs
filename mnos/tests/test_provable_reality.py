import unittest
from mnos.scripts.verify_shadow import verify_shadow_chain
from mnos.modules.shadow.service import shadow
from mnos.shared.execution_guard import in_sovereign_context

class TestProvableReality(unittest.TestCase):
    def setUp(self):
        shadow.chain = []
        shadow._seed_ledger()
        self.token = in_sovereign_context.set(True)

    def tearDown(self):
        in_sovereign_context.reset(self.token)

    def test_independent_auditor_pass(self):
        # 1. Valid chain should pass auditor
        shadow.commit("EVENT_1", {"v": 1})
        self.assertTrue(verify_shadow_chain(shadow.chain))

    def test_independent_auditor_fail_on_tamper(self):
        # 2. Tampered chain should fail auditor
        shadow.commit("EVENT_1", {"v": 1})
        shadow.chain[1]["payload"] = {"tampered": True}
        self.assertFalse(verify_shadow_chain(shadow.chain))

if __name__ == "__main__":
    unittest.main()
