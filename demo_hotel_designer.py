import json
from mnos.core.ai.parser import parse_prompt_to_request, BuildingRequest, Plot
from mnos.modules.compliance.checker import check_maldives_compliance
from mnos.modules.layout.generator import generate_layout
from mnos.modules.finance.boq import calculate_boq_and_cost

def run_demo(label, prompt_or_request):
    print(f"\n--- {label} ---")
    if isinstance(prompt_or_request, str):
        print(f"Prompt: \"{prompt_or_request}\"")
        request = parse_prompt_to_request(prompt_or_request)
    else:
        request = prompt_or_request
        print(f"Request: {request.plot.width}x{request.plot.depth}, {request.rooms_per_floor} rooms")

    compliance = check_maldives_compliance(request)
    print(f"Compliance: {'✅ OK' if compliance['is_compliant'] else '❌ FAIL'}")
    if not compliance['is_compliant']:
        print(f"Violations: {compliance['violations']}")
        return

    layout = generate_layout(request, compliance)
    if "error" in layout:
        print(f"Geometry Engine: ❌ {layout['error']}")
        return

    print(f"Geometry Engine: ✅ Deterministic Layout Generated ({len(layout['components'])} components)")
    print(f"Structural Grid: {layout['structural']['columns']} Columns, {layout['structural']['footings']} Footings")

    boq = calculate_boq_and_cost(layout)
    print(f"BOQ Estimate: {boq['currency']} {boq['total_estimate']:,}")
    print(f"Derived Steel: {boq['quantities']['steel_tons']} tons")

def main():
    print("🏛️ NEXUS ASI — Sovereign Construction Intelligence Layer")

    # Case 1: Omadhoo Spec (30x50, 5 rooms)
    run_demo("OMADHOO PRIME (Standard)", "1500 sqft, 30x50, 3 floors, 5 hotel rooms each floor, terrace")

    # Case 2: Impossible Plot (Too shallow)
    run_demo("IMPOSSIBLE PLOT (Depth Guard)", BuildingRequest(
        plot=Plot(width=30, depth=15), floors=1, rooms_per_floor=1, type="hotel"
    ))

    # Case 3: Narrow Plot (Single-loaded)
    run_demo("NARROW PLOT (Single-Loaded)", BuildingRequest(
        plot=Plot(width=20, depth=50), floors=2, rooms_per_floor=4, type="hotel"
    ))

if __name__ == "__main__":
    main()
