import unittest
from mnos.modules.aegis_bridge.bridge import get_signed_session_context
from mnos.core.security.aegis import aegis
import os

class TestBridgeAuth(unittest.TestCase):
    def test_signature_validation(self):
        context = get_signed_session_context()
        # This should pass if AEGIS is correctly configured
        self.assertTrue(aegis.validate_session(context))

if __name__ == "__main__":
    unittest.main()
