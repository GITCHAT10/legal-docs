import unittest
from mnos.core.ai.parser import BuildingRequest, Plot
from mnos.modules.compliance.checker import check_maldives_compliance
from mnos.modules.layout.generator import generate_layout

class TestHardenEngine(unittest.TestCase):
    def test_odd_room_counts(self):
        """Test counts like 5, 7, 9 use ceiling-based logic."""
        for count in [5, 7, 9]:
            request = BuildingRequest(plot=Plot(width=30, depth=50), floors=1, rooms_per_floor=count, type="hotel")
            compliance = check_maldives_compliance(request)
            layout = generate_layout(request, compliance)
            rooms = [c for c in layout["components"] if c["type"] == "room"]
            self.assertEqual(len(rooms), count)

    def test_small_plot_failure(self):
        """Test plot failure guard."""
        # Compliance should fail first for 30x15 plot (Usable depth 7ft)
        request = BuildingRequest(plot=Plot(width=30, depth=15), floors=1, rooms_per_floor=1, type="hotel")
        compliance = check_maldives_compliance(request)
        self.assertFalse(compliance["is_compliant"])
        self.assertIn("Impossible Plot: Usable depth <= 10ft guard.", compliance["violations"])

if __name__ == "__main__":
    unittest.main()
