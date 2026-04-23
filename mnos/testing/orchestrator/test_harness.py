import unittest
from mnos.modules.environment.orchestrator import env_orchestrator
from mnos.modules.atc.logic import atc_logic
from mnos.core.apollo.tax_governor import tax_governor
from mnos.core.ai.silvia import silvia
from decimal import Decimal

class TestApolloOrchestrator(unittest.TestCase):
    def test_tax_governor_mira_compliance(self):
        # MIRA Invoice test
        res = tax_governor.calculate_invoice(Decimal("100.00"), [], {})
        self.assertEqual(res["base"], Decimal("100.00"))
        self.assertEqual(res["service_charge"], Decimal("10.00"))
        self.assertEqual(res["taxable_amount"], Decimal("110.00"))
        self.assertEqual(res["tgst"], Decimal("18.70")) # 17% of 110
        self.assertEqual(res["total"], Decimal("128.70"))
        self.assertTrue(res["mira_compliant"])

    def test_atc_human_authority(self):
        # ATC Advisor test
        with patch("builtins.print") as mock_print:
            atc_logic.evaluate_flight_safety("TMA-123", {"wildlife_hazard": True})
            mock_print.assert_any_call("[ATC] Final clearance pending Human Controller Authority.")

    def test_silvia_suggestion_mode(self):
        # Forecast suggestion mode
        with patch("builtins.print") as mock_print:
            silvia.process_request("What is the shoreline readiness forecast?")
            mock_print.assert_any_call("[SILVIA] Suggestion Mode Active for forecast: What is the shoreline readiness forecast?")

from unittest.mock import patch
if __name__ == "__main__":
    unittest.main()
