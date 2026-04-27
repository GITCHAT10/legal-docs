import unittest
from decimal import Decimal
from mnos.modules.imoxon.pricing.engine import PricingEngine
from mnos.modules.finance.fce import FCEEngine

class TestPrestigePricing(unittest.TestCase):
    def setUp(self):
        self.fce = FCEEngine()
        self.pricing = PricingEngine(self.fce)

    def test_calculate_quote_usd_accommodation(self):
        # Net: 1000 USD
        # FX: 15.42 -> 15420 MVR
        # Margin: 15% -> 2313 MVR
        # Gross: 17733 MVR
        # FCE: Base 17733 + 10% SC (1773.30) + 17% TGST (3316.07) = 22822.37 MVR

        result = self.pricing.calculate_quote(
            net_amount=Decimal("1000"),
            currency="USD",
            category="ACCOMMODATION"
        )

        self.assertEqual(result["currency_orig"], "USD")
        self.assertEqual(result["net_mvr"], 15420.0)
        self.assertEqual(result["margin_pct"], 0.15)
        self.assertEqual(result["margin_amount"], 2313.0)
        self.assertEqual(result["gross_mvr"], 17733.0)

        fce = result["fce_breakdown"]
        self.assertEqual(fce["base"], 17733.0)
        self.assertEqual(fce["service_charge"], 1773.30)
        self.assertEqual(fce["subtotal"], 19506.30)
        self.assertEqual(fce["tax_amount"], 3316.07) # 17% of 19506.30
        self.assertEqual(result["total_mvr"], 22822.37)

    def test_commission_waterfall_splits(self):
        result = self.pricing.calculate_quote(
            net_amount=Decimal("1000"),
            currency="USD",
            category="TRANSFER"
        )
        # Net MVR: 15420
        # Margin: 10% -> 1542
        # Gross: 16962
        # Agent Commission: 10% of Gross -> 1696.20
        # Platform Fee: 2% of Gross -> 339.24

        self.assertEqual(result["gross_mvr"], 16962.0)
        self.assertEqual(result["agent_commission"], 1696.20)
        self.assertEqual(result["platform_fee"], 339.24)

    def test_fx_rate_update(self):
        self.pricing.update_fx_rate("USD", Decimal("16.00"))
        result = self.pricing.calculate_quote(
            net_amount=Decimal("1000"),
            currency="USD",
            category="DEFAULT"
        )
        self.assertEqual(result["net_mvr"], 16000.0)

    def test_allotment_override(self):
        # Net: 1000 USD -> 15420 MVR
        # Override: +5% -> 16191 MVR
        # Margin: 10% -> 1619.10 MVR
        # Gross: 17810.10 MVR
        result = self.pricing.calculate_quote(
            net_amount=Decimal("1000"),
            currency="USD",
            category="DEFAULT",
            allotment_override_pct=Decimal("0.05")
        )
        self.assertEqual(result["net_mvr"], 15420.0)
        self.assertEqual(result["gross_mvr"], 17810.10)

if __name__ == "__main__":
    unittest.main()
