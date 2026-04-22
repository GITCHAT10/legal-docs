import unittest
from mnos.core.ai.parser import BuildingRequest, Plot
from mnos.modules.compliance.checker import check_maldives_compliance
from mnos.modules.layout.generator import generate_layout

class TestNexusEngine(unittest.TestCase):
    def test_30x50_5rooms_odd_count(self):
        """Test the Omadhoo spec: 30x50 plot with 5 rooms (Odd count)."""
        request = BuildingRequest(
            plot=Plot(width=30, depth=50),
            floors=3,
            rooms_per_floor=5,
            type="hotel"
        )
        compliance = check_maldives_compliance(request)
        self.assertTrue(compliance["is_compliant"])

        layout = generate_layout(request, compliance)
        self.assertNotIn("error", layout)

        # 5 rooms should result in 3 rows (ceil(5/2))
        rooms = [c for c in layout["components"] if c["type"] == "room"]
        self.assertEqual(len(rooms), 5)

        # Verify no negative dimensions
        for comp in layout["components"]:
            if "dimensions" in comp:
                self.assertGreater(comp["dimensions"]["width"], 0)
                self.assertGreater(comp["dimensions"]["depth"], 0)

    def test_impossible_depth_guard(self):
        """Test the CEO Directive: reject usable depth < 12ft."""
        # Plot depth 19ft - 8ft setbacks = 11ft usable (Below 12ft threshold)
        request = BuildingRequest(
            plot=Plot(width=30, depth=19),
            floors=1,
            rooms_per_floor=1,
            type="hotel"
        )
        compliance = check_maldives_compliance(request)
        self.assertFalse(compliance["is_compliant"])
        self.assertIn("Impossible Geometry: Usable depth < 12ft", compliance["violations"][0])

    def test_tight_width_single_loaded(self):
        """Test that narrow plots switch to single-loaded corridor."""
        # 20ft plot - 6ft setbacks = 14ft usable
        # Double loaded needs: 8 (room) + 4 (corridor) + 8 (room) = 20ft. 14ft < 20ft.
        request = BuildingRequest(
            plot=Plot(width=20, depth=50),
            floors=1,
            rooms_per_floor=2,
            type="hotel"
        )
        compliance = check_maldives_compliance(request)
        layout = generate_layout(request, compliance)

        rooms = [c for c in layout["components"] if c["type"] == "room"]
        # In single loaded, room width should be usable_width - corridor_width
        # 14 - 4 = 10ft
        self.assertEqual(rooms[0]["dimensions"]["width"], 10)
        self.assertEqual(rooms[0]["position"]["x"], 0)

if __name__ == "__main__":
    unittest.main()
