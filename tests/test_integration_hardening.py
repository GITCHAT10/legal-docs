import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from skyfarm.main import app
import requests
import os

client = TestClient(app)

class TestIntegrationHardening(unittest.TestCase):
    def setUp(self):
        os.environ["SKYFARM_INTEGRATION_SECRET"] = "test_secret"
        os.environ["MNOS_INTEGRATION_SECRET"] = "test_secret"

    @patch("skyfarm.integration.router.session.post")
    def test_mnos_401_propagation(self, mock_post):
        # Simulate 401 from MNOS
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "INVALID_SIGNATURE"
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
    def test_mnos_timeout_propagation(self, mock_post):
        # Simulate timeout
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

    @patch("skyfarm.integration.router.session.post")
    def test_mnos_502_propagation(self, mock_post):
        # Simulate connection error
        mock_post.side_effect = requests.exceptions.ConnectionError("Failed to connect")

        payload = {
            "tenant_id": "sf_01",
            "event_type": "TEST",
            "category": "trace",
            "data": {"val": 1}
        }

        response = client.post("/integration/v1/send", json=payload)
        self.assertEqual(response.status_code, 502)
        self.assertIn("MNOS connection error", response.json()["detail"])

if __name__ == "__main__":
    unittest.main()
