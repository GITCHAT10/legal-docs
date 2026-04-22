import unittest
from unittest.mock import MagicMock, patch
import json
import os
from mnos.modules.aegis_bridge.bridge import sign_payload, SESSION_CONTEXT
from mnos.core.security.aegis import aegis

class TestBridgeAuth(unittest.TestCase):
    def test_signature_validation(self):
        # The bridge uses NEXGEN_SECRET to sign
        # AEGIS uses config.NEXGEN_SECRET to validate
        # We need to ensure they match or are correctly set in the environment

        secret = os.getenv("NEXGEN_SECRET", "hardened_secret_placeholder")

        payload = {"device_id": "MIG-AIGM-2024PV12395H", "role": "security_bridge"}
        sig = sign_payload(payload)

        context = payload.copy()
        context["signature"] = sig

        # This should pass if AEGIS is correctly configured
        self.assertTrue(aegis.validate_session(context))

if __name__ == "__main__":
    unittest.main()
