import unittest
import os
from decimal import Decimal
from datetime import datetime
from mnos.modules.fce.service import fce

class TestMiraFiscalLogic(unittest.TestCase):
    def test_tgst_pre_transition(self):
        # Pre 2025-07-01
        stay_date = datetime(2025, 6, 30)
        res = fce.calculate_taxes(Decimal("1000.00"), stay_date=stay_date)
        # 1000 + 100 (SC) = 1100. 1100 * 0.16 = 176.
        self.assertEqual(res["tgst_rate"], Decimal("0.16"))
        self.assertEqual(res["tgst"], Decimal("176.00"))

    def test_tgst_post_transition(self):
        # Post 2025-07-01
        stay_date = datetime(2025, 7, 1)
        res = fce.calculate_taxes(Decimal("1000.00"), stay_date=stay_date)
        # 1000 + 100 (SC) = 1100. 1100 * 0.17 = 187.
        self.assertEqual(res["tgst_rate"], Decimal("0.17"))
        self.assertEqual(res["tgst"], Decimal("187.00"))

    def test_green_tax_exemptions(self):
        res = fce.calculate_taxes(Decimal("1000.00"), pax=2, pax_under_2=1, nights=1, apply_green_tax=True)
        # 1 effective pax * 6 USD = 6 USD
        self.assertEqual(res["green_tax"], Decimal("6.00"))

    def test_green_tax_guesthouse(self):
        res = fce.calculate_taxes(Decimal("1000.00"), pax=2, nights=1, apply_green_tax=True, is_guesthouse=True)
        # 2 pax * 3 USD = 6 USD
        self.assertEqual(res["green_tax"], Decimal("6.00"))

if __name__ == "__main__":
    os.environ["NEXGEN_SECRET"] = "STAGING_SECRET"
    unittest.main()
