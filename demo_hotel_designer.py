import asyncio
import json
from mnos.modules.layout.generator import sie
from mnos.modules.finance.boq import boq_engine
from mnos.modules.compliance.checker import compliance
from mnos.modules.gis.engine import gis_engine
from mnos.modules.shadow.service import shadow

async def test_pipeline():
    print("--- STARTING NEXUS ASI PIPELINE TEST ---")

    # 1. GIS Check
    island = "Maafushi"
    island_data = gis_engine.get_island_data(island)
    print(f"GIS Data for {island}: {island_data}")

    # 2. Geometry Generation
    plot_w, plot_d, rooms = 30, 50, 10
    layout = sie.generate_layout(plot_w, plot_d, rooms)
    print(f"Layout Generated: {layout}")

    # 3. Compliance
    total_area = plot_w * plot_d * 2
    comp = compliance.verify_compliance(total_area, plot_w * plot_d, 2, layout["rooms_per_floor"])
    print(f"Compliance Check: {comp}")

    # 4. BOQ & Fiscal
    boq = boq_engine.generate_boq(layout, 2)
    print(f"BOQ (inc. MOATS): {json.dumps(boq, indent=2)}")

    # 5. Shadow Audit
    shadow.commit("test_001", "PIPELINE_TEST", {"status": "SUCCESS"})
    print(f"Shadow Integrity: {shadow.verify_integrity()}")

    print("--- PIPELINE TEST PASSED ---")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
