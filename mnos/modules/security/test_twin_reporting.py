import unittest
from mnos.modules.security.service import security_module
from mnos.modules.shadow.service import shadow
from mnos.core.security.aegis import aegis
import json
import hmac
import hashlib
from mnos.config import config

class TestTwinReporting(unittest.TestCase):
    def setUp(self):
        shadow.chain = shadow.chain[:1]
        self.session_payload = {"device_id": "MIG-AIGM-2024PV12395H", "role": "security_bridge"}
        self.session_context = self.session_payload.copy()
        self.session_context["signature"] = aegis.sign_session(self.session_payload)

    def test_security_event_carries_twin_reporting(self):
        # Simulate a TL-3 detection with reporting metadata
        event_data = {
            "frigate_event": {
                "after": {
                    "confidence": 0.95,
                    "label": "person",
                    "current_zones": ["Sala_Fushi_Perimeter"],
                    "duration": 200
                }
            },
            "multi_signal_vetted": True, # Required by APOLLO
            "reporting_metadata": {
                "reporting_currency_usd": "USD",
                "reporting_currency_local": "MVR",
                "reporting_amount_usd": 100.0,
                "reporting_amount_local": 1542.0,
                "reporting_fx_rate_locked": 15.42,
                "reporting_jurisdiction": "MV"
            }
        }

        security_module.process_security_event(event_data, self.session_context)

        alert_entry = [e for e in shadow.chain if e["event_type"] == "nexus.security.alert"][0]
        metadata = alert_entry["payload"]["data"]["input"]["reporting_metadata"]

        self.assertEqual(metadata["reporting_currency_usd"], "USD")
        self.assertEqual(metadata["reporting_amount_local"], 1542.0)
        self.assertEqual(metadata["reporting_jurisdiction"], "MV")

if __name__ == "__main__":
    unittest.main()
