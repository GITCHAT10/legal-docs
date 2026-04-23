import unittest
from unittest.mock import MagicMock, patch
import json
import os
import hmac
import hashlib
from mnos.modules.security.service import security_module
from mnos.core.events.service import events
from mnos.modules.shadow.service import shadow
from mnos.core.security.aegis import aegis
from mnos.config import config

class TestSecurityAutonomousResponse(unittest.TestCase):
    def setUp(self):
        # Reset shadow for clean state
        shadow.chain = shadow.chain[:1]
        self.session_context = {
            "device_id": "MIG-AIGM-2024PV12395H",
            "role": "security_bridge"
        }
        # Real signature for tests
        data = json.dumps(self.session_context, sort_keys=True).encode()
        self.session_context["signature"] = hmac.new(config.NEXGEN_SECRET.encode(), data, hashlib.sha256).hexdigest()

    @patch("mnos.core.security.aegis.AegisService.validate_session", return_value=True)
    def test_tl5_critical(self, mock_val):
        # System interference
        event_data = {
            "frigate_event": {
                "after": {
                    "is_blinded": True,
                    "confidence": 0.995, # Required by APOLLO for TL-5
                    "current_zones": ["Sala_Fushi_Perimeter"]
                }
            }
        }
        with patch("builtins.print") as mock_print:
            security_module.process_security_event(event_data, self.session_context)
            mock_print.assert_any_call("[APOLLO] POLICY GRANTED")
            mock_print.assert_any_call("[Security] TL-5 RESPONSE: SYSTEM INTERFERENCE DETECTED")

    @patch("mnos.core.security.aegis.AegisService.validate_session", return_value=True)
    def test_tl4_enforcement(self, mock_val):
        # Breach of restricted zone
        event_data = {
            "frigate_event": {
                "after": {
                    "confidence": 0.96, # Required by APOLLO for TL-4
                    "current_zones": ["Restricted_Staff_Only"]
                }
            }
        }
        with patch("builtins.print") as mock_print:
            security_module.process_security_event(event_data, self.session_context)
            mock_print.assert_any_call("[APOLLO] POLICY GRANTED")
            mock_print.assert_any_call("[Security] TL-4 RESPONSE for zone: Restricted_Staff_Only")

    @patch("mnos.core.security.aegis.AegisService.validate_session", return_value=True)
    def test_tl3_alert(self, mock_val):
        # Loitering
        event_data = {
            "frigate_event": {
                "after": {
                    "duration": 200,
                    "confidence": 0.91, # Required by APOLLO for TL-3
                    "current_zones": ["Sala_Fushi_Perimeter"]
                }
            }
        }
        with patch("builtins.print") as mock_print:
            security_module.process_security_event(event_data, self.session_context)
            mock_print.assert_any_call("[APOLLO] POLICY GRANTED")
            mock_print.assert_any_call("[Security] TL-3 RESPONSE for zone: Sala_Fushi_Perimeter")

    @patch("mnos.core.security.aegis.AegisService.validate_session", return_value=True)
    def test_tl2_verify(self, mock_val):
        # Unknown person
        event_data = {
            "frigate_event": {
                "after": {
                    "confidence": 0.85,
                    "is_known": False,
                    "current_zones": ["Sala_Fushi_Perimeter"]
                }
            }
        }
        with patch("builtins.print") as mock_print:
            security_module.process_security_event(event_data, self.session_context)
            mock_print.assert_any_call("[Security] ALERT: TL-2 Verification needed in Sala_Fushi_Perimeter. Person detected.")

    @patch("mnos.core.security.aegis.AegisService.validate_session", return_value=True)
    def test_apollo_rejection(self, mock_val):
        # Low confidence TL-3 should be blocked
        event_data = {
            "frigate_event": {
                "after": {
                    "duration": 200,
                    "confidence": 0.80, # Below 0.90 for TL-3
                    "current_zones": ["Sala_Fushi_Perimeter"]
                }
            }
        }
        with patch("builtins.print") as mock_print:
            security_module.process_security_event(event_data, self.session_context)
            mock_print.assert_any_call("[Security] ACTION BLOCKED BY APOLLO POLICY PLANE")

if __name__ == "__main__":
    unittest.main()
