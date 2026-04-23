import unittest
import json
import hmac
import hashlib
from mnos.core.security.aegis import aegis, SecurityException
from mnos.config import config

class TestAegisHsmHardening(unittest.TestCase):
    def setUp(self):
        self.root_uei = "2024PV12395H"

    def test_hsm_signed_privileged_session_acceptance(self):
        # HSM-signed privileged session
        payload = {"device_id": self.root_uei, "role": "privileged"}
        sig = aegis.sign_session(payload)
        context = payload.copy()
        context["signature"] = sig

        self.assertTrue(aegis.validate_session(context))
        self.assertEqual(context["bound_device_id"], self.root_uei)

    def test_unsigned_privileged_session_rejection(self):
        context = {"device_id": self.root_uei, "role": "privileged"}
        with self.assertRaises(SecurityException) as cm:
            aegis.validate_session(context)
        self.assertIn("Missing session signature", str(cm.exception))

    def test_forged_device_binding_rejection(self):
        # Privileged role attempted by non-HSM device
        payload = {"device_id": "nexus-001", "role": "privileged"}
        sig = aegis.sign_session(payload)
        context = payload.copy()
        context["signature"] = sig

        with self.assertRaises(SecurityException) as cm:
            aegis.validate_session(context)
        self.assertIn("Privileged session rejected", str(cm.exception))

    def test_server_side_binding_enforcement(self):
        # Client tries to inject bound_device_id
        payload = {"device_id": "nexus-001", "role": "user"}
        sig = aegis.sign_session(payload)
        context = payload.copy()
        context["signature"] = sig
        context["bound_device_id"] = "ADMIN-IDENTITY"

        aegis.validate_session(context)
        # Should be overwritten by server lookup
        self.assertEqual(context["bound_device_id"], "nexus-001")

if __name__ == "__main__":
    unittest.main()
