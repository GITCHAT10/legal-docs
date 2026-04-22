import unittest
import os
from decimal import Decimal
from datetime import datetime
from mnos.modules.fce.service import fce
from mnos.modules.shadow.service import shadow
from mnos.core.security.aegis import aegis

class StagingTestMatrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["NEXGEN_SECRET"] = "STAGING_SECRET"

    def test_tgst_transition(self):
        # Pre-transition
        pre = fce.calculate_taxes(Decimal("1000.00"), stay_date=datetime(2025, 6, 29))
        self.assertEqual(pre["tgst"], Decimal("176.00")) # 16% of 1100

        # Post-transition
        post = fce.calculate_taxes(Decimal("1000.00"), stay_date=datetime(2025, 7, 2))
        self.assertEqual(post["tgst"], Decimal("187.00")) # 17% of 1100

    def test_invoice_issued_before_stay(self):
        # Time of supply is key.
        # If invoice issued today (pre-transition) but stay is post-transition.
        stay_date = datetime(2025, 8, 1)
        res = fce.calculate_taxes(Decimal("1000.00"), stay_date=stay_date)
        self.assertEqual(res["tgst_rate"], Decimal("0.17"))

    def test_green_tax_under_2_exemption(self):
        res = fce.calculate_taxes(Decimal("0.00"), pax=3, pax_under_2=2, nights=5, apply_green_tax=True)
        # 1 effective pax * 6 USD * 5 nights = 30 USD
        self.assertEqual(res["green_tax"], Decimal("30.00"))

    def test_shadow_genesis_tamper(self):
        # Verify detection
        shadow.chain = []
        shadow._seed_ledger()
        self.assertTrue(shadow.verify_integrity())

        shadow.chain[0]["event_type"] = "TAMPERED"
        self.assertFalse(shadow.verify_integrity())

    def test_efaas_consent_validation(self):
        # Valid flow
        payload = aegis.authenticate_efaas("VALID-CODE")
        self.assertTrue(payload["consent_confirmed"])

        # Simulated rebind
        success = aegis.rebind_device("MV-ID-123", "HW-MALDIVES-NEXUS-REBIND-001")
        self.assertTrue(success)

if __name__ == "__main__":
    unittest.main()
