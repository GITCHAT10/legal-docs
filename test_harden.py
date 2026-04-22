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
        # 30x15 plot -> 15-8 = 7ft usable depth. Pre-layout validator should block <= 10ft.
        request = BuildingRequest(plot=Plot(width=30, depth=15), floors=1, rooms_per_floor=1, type="hotel")
        compliance = check_maldives_compliance(request)
        layout = generate_layout(request, compliance)
        self.assertIn("error", layout)
        self.assertEqual(layout["status"], "FAIL_CLOSED")

    def test_inn_compatibility(self):
        """Test INN room inventory schema output."""
        request = BuildingRequest(plot=Plot(width=30, depth=50), floors=2, rooms_per_floor=4, type="hotel")
        compliance = check_maldives_compliance(request)
        layout = generate_layout(request, compliance)
        self.assertIn("inn_inventory", layout)
        self.assertEqual(len(layout["inn_inventory"]), 4)

if __name__ == "__main__":
    unittest.main()
