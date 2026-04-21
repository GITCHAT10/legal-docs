import json
from mnos.core.ai.parser import parse_prompt_to_request, BuildingRequest, Plot
from mnos.modules.compliance.checker import check_maldives_compliance
from mnos.modules.layout.generator import generate_layout
from mnos.modules.finance.boq import calculate_boq_and_cost
from mnos.modules.finance.sxos_adapter import release_sxos_wave_2

def run_demo(label, prompt_or_request):
    print(f"\n--- {label} ---")
    if isinstance(prompt_or_request, str):
        print(f"Prompt: \"{prompt_or_request}\"")
        request = parse_prompt_to_request(prompt_or_request)
    else:
        request = prompt_or_request
        print(f"Request: {request.plot.width}x{request.plot.depth}, {request.rooms_per_floor} rooms")

    # 1. Compliance
    compliance = check_maldives_compliance(request)
    print(f"Compliance: {'✅ OK' if compliance['is_compliant'] else '❌ FAIL'}")
    if not compliance['is_compliant']:
        print(f"Violations: {compliance['violations']}")
        return

    # 2. Geometry
    layout = generate_layout(request, compliance)
    if "error" in layout:
        print(f"Geometry Engine: ❌ {layout['error']}")
        return
    print(f"Geometry Engine: ✅ Deterministic Layout Generated ({len(layout['components'])} components)")

    # 3. BOQ
    boq = calculate_boq_and_cost(layout)
    print(f"BOQ Estimate: {boq['currency']} {boq['total_estimate']:,}")

    # 4. SXOS WAVE 2 RELEASE (NEW)
    print("\n[🚀 SXOS WAVE 2 TRIGGER]")
    sxos_result = release_sxos_wave_2(boq)
    print(f"Status: {sxos_result['status']}")
    if "procurement" in sxos_result:
        p = sxos_result['procurement']
        print(f"Supply Chain: {p['material']} ({p['quantity']})")
        print(f"Supplier: {p['supplier']} | ID: {p['order_id']}")
        print(f"Action: {sxos_result['action']}")
    else:
        print(f"Action: {sxos_result['status']} | Reason: {sxos_result.get('reason')}")

def main():
    print("🏛️ NEXUS ASI — Sovereign Construction Intelligence Layer")
    print("Design-to-Order Pipeline (BIM -> SXOS)")

    # Successful Case: Omadhoo
    run_demo("OMADHOO PRIME (Validated Design)", "1500 sqft, 30x50, 3 floors, 5 hotel rooms each floor, terrace")

    # Failure Case: Impossible Depth
    run_demo("IMPOSSIBLE BUILD (Hard Block)", BuildingRequest(
        plot=Plot(width=30, depth=15), floors=1, rooms_per_floor=1, type="hotel"
    ))

if __name__ == "__main__":
    main()
