import unittest
from decimal import Decimal
from mnos.modules.imoxon.pricing.engine import PricingEngine, ProductType, Channel
from mnos.modules.finance.fce import FCEEngine, TaxType

class TestPrestigePricing(unittest.TestCase):
    def setUp(self):
        self.fce = FCEEngine()
        self.pricing = PricingEngine(self.fce)

    def test_calculate_quote_maldives_standard(self):
        # 1000 USD -> 15420 MVR
        # Accommodation Margin 15% -> 2313 MVR
        # Gross: 17733 MVR
        # Tax: TOURISM_STANDARD (17% TGST on Subtotal)
        # SC: 10% of 17733 = 1773.30
        # Subtotal: 19506.30
        # TGST: 17% of 19506.30 = 3316.07
        # Total: 22822.37

        result = self.pricing.calculate_quote(
            net_amount=Decimal("1000"),
            currency="USD",
            product_type=ProductType.ACCOMMODATION,
            trace_id="T-123",
            tax_type=TaxType.TOURISM_STANDARD
        )

        self.assertEqual(result["breakdown"]["trace_id"], "T-123")
        self.assertEqual(result["breakdown"]["service_charge"], 1773.30)
        self.assertEqual(result["breakdown"]["tgst"], 3316.07)
        self.assertEqual(result["total_mvr"], 22822.37)

    def test_retail_tax_path(self):
        # RETAIL (8% GST)
        # Gross: 17733 MVR
        # SC: 1773.30 -> Subtotal: 19506.30
        # GST: 8% of 19506.30 = 1560.50
        # Total: 21066.80
        result = self.pricing.calculate_quote(
            net_amount=Decimal("1000"),
            currency="USD",
            product_type=ProductType.ACCOMMODATION,
            trace_id="T-RETAIL",
            tax_type=TaxType.RETAIL
        )
        self.assertEqual(result["breakdown"]["tgst"], 1560.50)
        self.assertEqual(result["total_mvr"], 21066.80)

    def test_missing_or_zero_amount_fails(self):
        with self.assertRaises(ValueError):
            self.pricing.calculate_quote(Decimal("0"), "USD", ProductType.ACTIVITY, "T-ZERO")

    def test_pricing_breakdown_completeness(self):
        result = self.pricing.calculate_quote(
            net_amount=Decimal("500"),
            currency="USD",
            product_type=ProductType.TRANSFER_SEA,
            trace_id="T-TRACE"
        )
        b = result["breakdown"]
        required = ["base_price", "cost_price", "margin_pct", "commission_b2b", "service_charge", "tgst", "trace_id"]
        for key in required:
            self.assertIn(key, b)

if __name__ == "__main__":
    unittest.main()
