import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from skyfarm.main import app
import requests
import os

client = TestClient(app)

class TestIntegrationFailurePaths(unittest.TestCase):
    def setUp(self):
        os.environ["SKYFARM_INTEGRATION_SECRET"] = "test_secret"
        os.environ["MNOS_INTEGRATION_SECRET"] = "test_secret"

    @patch("skyfarm.integration.router.session.post")
    def test_mnos_401_rejection(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "UNAUTHORIZED"
        mock_post.return_value = mock_response

        payload = {
            "tenant_id": "sf_01",
            "event_type": "TEST",
            "category": "trace",
            "data": {"val": 1}
        }
        response = client.post("/integration/v1/send", json=payload)
        self.assertEqual(response.status_code, 401)
        self.assertIn("MNOS rejected request", response.json()["detail"])

    @patch("skyfarm.integration.router.session.post")
    def test_mnos_timeout(self, mock_post):
        mock_post.side_effect = requests.exceptions.Timeout()
        payload = {
            "tenant_id": "sf_01",
            "event_type": "TEST",
            "category": "trace",
            "data": {"val": 1}
        }
        response = client.post("/integration/v1/send", json=payload)
        self.assertEqual(response.status_code, 504)
        self.assertEqual(response.json()["detail"], "MNOS integration timeout")

    @patch("skyfarm.integration.router.verify_signature_v2")
    def test_invalid_carbon_signature(self, mock_verify):
        mock_verify.return_value = False
        payload = {
            "guest_name": "Aman",
            "amount_kg": 14.5
        }
        headers = {
            "X-Signature": "invalid",
            "X-Timestamp": "2026-04-19T12:00:00Z",
            "X-Request-Id": "req_1"
        }
        response = client.post("/integration/v1/carbon/retire", json=payload, headers=headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "INVALID_SOVEREIGN_SIGNATURE")

if __name__ == "__main__":
    unittest.main()
