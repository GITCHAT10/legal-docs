import unittest
from decimal import Decimal
from mnos.modules.imoxon.pricing.engine import PricingEngine, TaxContext, Channel
from mnos.modules.finance.fce import FCEEngine

class TestPrestigePricing(unittest.TestCase):
    def setUp(self):
        self.fce = FCEEngine()
        self.pricing = PricingEngine(self.fce)

    def test_calculate_quote_usd_tourism(self):
        # Net: 1000 USD -> 15420 MVR
        # Margin: 15% -> 2313 MVR
        # Gross: 17733 MVR
        # FCE TOURISM: 10% SC (1773.30) + 17% TGST (3316.07) = 22822.37 MVR

        result = self.pricing.calculate_quote(
            net_amount=Decimal("1000"),
            currency="USD",
            category="ACCOMMODATION",
            tax_context=TaxContext.TOURISM
        )

        self.assertEqual(result["price_trace"]["tax_context"], "TOURISM")
        self.assertEqual(result["fce_breakdown"]["tax_rate"], 0.17)
        self.assertEqual(result["total_mvr"], 22822.37)

    def test_calculate_quote_retail_tax(self):
        # Gross: 17733 MVR
        # FCE RETAIL: 10% SC (1773.30) + 8% GST (1560.50) = 21066.80 MVR

        result = self.pricing.calculate_quote(
            net_amount=Decimal("1000"),
            currency="USD",
            category="ACCOMMODATION",
            tax_context=TaxContext.RETAIL
        )

        self.assertEqual(result["price_trace"]["tax_context"], "RETAIL")
        self.assertEqual(result["fce_breakdown"]["tax_rate"], 0.08)
        self.assertEqual(result["total_mvr"], 21066.80)

    def test_missing_or_zero_amount_fails(self):
        with self.assertRaises(ValueError):
            self.pricing.calculate_quote(Decimal("0"), "USD", "DEFAULT")
        with self.assertRaises(ValueError):
            self.pricing.calculate_quote(Decimal("-10"), "USD", "DEFAULT")

    def test_channel_ota_markup(self):
        # Net: 1000 USD -> 15420 MVR
        # OTA Markup: +10% -> 16962 MVR
        # Margin: 10% on 16962 -> 1696.20
        # Gross: 18658.20 MVR
        result = self.pricing.calculate_quote(
            net_amount=Decimal("1000"),
            currency="USD",
            category="DEFAULT",
            channel=Channel.OTA
        )
        self.assertEqual(result["price_trace"]["channel"], "OTA")
        self.assertEqual(result["price_trace"]["channel_modifier"], 1.1)
        self.assertEqual(result["gross_mvr"], 18658.20)

    def test_channel_sovereign_discount(self):
        # Net: 1000 USD -> 15420 MVR
        # Sovereign Discount: -5% -> 14649 MVR
        # Margin: 10% on 14649 -> 1464.90
        # Gross: 16113.90 MVR
        result = self.pricing.calculate_quote(
            net_amount=Decimal("1000"),
            currency="USD",
            category="DEFAULT",
            channel=Channel.SOVEREIGN
        )
        self.assertEqual(result["price_trace"]["channel"], "SOVEREIGN")
        self.assertEqual(result["price_trace"]["channel_modifier"], 0.95)
        self.assertEqual(result["gross_mvr"], 16113.90)

    def test_price_trace_completeness(self):
        result = self.pricing.calculate_quote(
            net_amount=Decimal("500"),
            currency="USD",
            category="TRANSFER"
        )
        trace = result["price_trace"]
        self.assertIn("net_orig", trace)
        self.assertIn("margin_pct", trace)
        self.assertIn("fx_rate", trace)
        self.assertIn("fce_breakdown", trace)
        self.assertEqual(trace["tax_context"], "TOURISM")

    def test_maldives_billing_rule_enforced(self):
        # Ensure SC is added before Tax is calculated
        result = self.pricing.calculate_quote(
            net_amount=Decimal("1000"),
            currency="USD",
            category="DEFAULT"
        )
        fce = result["fce_breakdown"]
        base = Decimal(str(fce["base"]))
        sc = Decimal(str(fce["service_charge"]))
        subtotal = Decimal(str(fce["subtotal"]))
        tax = Decimal(str(fce["tax_amount"]))
        tax_rate = Decimal(str(fce["tax_rate"]))

        self.assertEqual(subtotal, base + sc)
        self.assertEqual(tax, (subtotal * tax_rate).quantize(Decimal("0.01")))

if __name__ == "__main__":
    unittest.main()
