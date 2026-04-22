import unittest
from unittest.mock import MagicMock, patch
import json
from mnos.modules.security.service import security_module
from mnos.core.events.service import events
from mnos.modules.shadow.service import shadow

class TestSecurityAutonomousResponse(unittest.TestCase):
    def setUp(self):
        # Reset shadow for clean state
        shadow.chain = shadow.chain[:1]
        self.session_context = {
            "device_id": "MIG-AIGM-2024PV12395H",
            "signature": "valid_sig"
        }

    @patch("mnos.core.security.aegis.AegisService.validate_session", return_value=True)
    def test_tl3_lockdown_and_alert(self, mock_validate):
        # High confidence person detection
        event_data = {
            "frigate_event": {
                "after": {
                    "confidence": 0.95,
                    "label": "person",
                    "current_zones": ["Sala_Fushi_Perimeter"]
                }
            }
        }

        # Capture print output or use mocks
        with patch("builtins.print") as mock_print:
            security_module.process_security_event(event_data, self.session_context)

            # Verify lockdown call
            mock_print.assert_any_call("[Security] LOCKDOWN INITIATED for zone: Sala_Fushi_Perimeter")
            mock_print.assert_any_call("[Security] ACTION: Perimeter doors ENTRY RESTRICTED. EXIT REMAINS OPEN.")

            # Verify alert call
            mock_print.assert_any_call("[Security] ALERT: Threat Level 3 detected in Sala_Fushi_Perimeter. Perimeter secured.")

        # Verify SHADOW ledger entries
        # entry 0 is GENESIS
        # entry 1 is lockdown
        # entry 2 is alert
        self.assertEqual(len(shadow.chain), 3)
        self.assertEqual(shadow.chain[1]["event_type"], "nexus.security.lockdown")
        self.assertEqual(shadow.chain[2]["event_type"], "nexus.security.alert")

    @patch("mnos.core.security.aegis.AegisService.validate_session", return_value=True)
    def test_tl2_verify(self, mock_validate):
        # Medium confidence detection
        event_data = {
            "frigate_event": {
                "after": {
                    "confidence": 0.80,
                    "label": "person",
                    "current_zones": ["Sala_Fushi_Perimeter"]
                }
            }
        }

        with patch("builtins.print") as mock_print:
            security_module.process_security_event(event_data, self.session_context)
            mock_print.assert_any_call("[Security] ALERT: Verify activity in Sala_Fushi_Perimeter. Level 2 confidence.")

        self.assertEqual(len(shadow.chain), 2)
        self.assertEqual(shadow.chain[1]["event_type"], "nexus.security.alert")

if __name__ == "__main__":
    unittest.main()
