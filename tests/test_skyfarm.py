import unittest
from skyfarm.identity.models import UserModel, Role
from skyfarm.integration.service import create_integration_event, verify_signature_v2, generate_canonical_string, sign_payload_canonical, SECRET_KEY
from skyfarm.finance.service import calculate_maldives_pricing
import uuid
import hashlib
import json
from datetime import datetime, timezone

class TestSkyfarm(unittest.TestCase):
    def test_identity_models(self):
        user = UserModel(id="u1", username="captain1", role=Role.CAPTAIN, org_id="org1")
        self.assertEqual(user.username, "captain1")

    def test_finance_pricing(self):
        # Base 1000 + 10% (100) = 1100. 1100 + 17% (187) = 1287.
        pricing = calculate_maldives_pricing(1000.0)
        self.assertEqual(pricing["service_charge"], 100.0)
        self.assertEqual(pricing["tgst"], 187.0)
        self.assertEqual(pricing["total"], 1287.0)

    def test_canonical_signing(self):
        body = {"test": "data"}
        timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        request_id = "req1"
        method = "POST"
        path = "/test"

        body_bytes = json.dumps(body, sort_keys=True).encode()
        canonical = generate_canonical_string(method, path, timestamp, request_id, body_bytes)
        signature = sign_payload_canonical(canonical, SECRET_KEY)

        valid = verify_signature_v2(signature, method, path, timestamp, request_id, body, SECRET_KEY)
        self.assertTrue(valid)

if __name__ == "__main__":
    unittest.main()
