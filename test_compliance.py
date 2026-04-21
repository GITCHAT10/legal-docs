import unittest
from mnos.core.ai.parser import BuildingRequest, Plot
from mnos.modules.compliance.checker import check_maldives_compliance

class TestCompliance(unittest.TestCase):
    def test_compliant_hotel(self):
        request = BuildingRequest(
            plot=Plot(width=30, depth=50),
            floors=3,
            rooms_per_floor=5,
            type="hotel"
        )
        result = check_maldives_compliance(request)
        self.assertTrue(result["is_compliant"])
        self.assertEqual(len(result["violations"]), 0)
        self.assertGreater(len(result["recommendations"]), 0)

    def test_non_compliant_plot(self):
        # Extremely small plot
        request = BuildingRequest(
            plot=Plot(width=5, depth=5),
            floors=1,
            rooms_per_floor=1,
            type="hotel"
        )
        result = check_maldives_compliance(request)
        self.assertFalse(result["is_compliant"])
        self.assertIn("Plot size too small for mandatory setbacks.", result["violations"])

if __name__ == "__main__":
    unittest.main()
