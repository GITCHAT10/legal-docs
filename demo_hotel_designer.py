import json
from mnos.core.ai.parser import parse_prompt_to_request, BuildingRequest, Plot
from mnos.modules.compliance.checker import check_maldives_compliance
from mnos.modules.layout.generator import generate_layout
from mnos.modules.finance.boq import calculate_boq_and_cost
from mnos.modules.finance.sxos_adapter import release_sxos_wave_2
from mnos.modules.interior.designer import scan_room_ar

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
        return

    # 2. Geometry + Interior Smart Wizard
    layout = generate_layout(request, compliance)
    if "error" in layout:
        print(f"Engine Error: ❌ {layout['error']}")
        return
    print(f"Geometry Engine: ✅ Layout + Interiors Generated ({len(layout['interiors'])} furnished rooms)")

    # Showcase one furnished room
    if layout["interiors"]:
        room = layout["interiors"][0]
        print(f"\n[🏠 INTERIOR AI WIZARD - {room['room_id']}]")
        print(f"Render Mode: {room['render_mode']}")
        print(f"Automated Furniture (Smart Placement):")
        for f in room['furniture']:
            print(f" - {f['item']} ({f['brand']})")

    # 3. BOQ (Structural + Interior)
    boq = calculate_boq_and_cost(layout)
    print(f"\n[📊 BOQ - CONSOLIDATED ESTIMATE]")
    print(f"Furniture Cost: {boq['currency']} {boq['costs']['furniture']:,}")
    print(f"Structural Steel: {boq['quantities']['steel_tons']} Tons")
    print(f"Total Project Estimate: {boq['currency']} {boq['total_estimate']:,}")

    # 4. SXOS WAVE 2 RELEASE
    print("\n[🚀 SXOS WAVE 2 TRIGGER]")
    sxos_result = release_sxos_wave_2(boq)
    print(f"Status: {sxos_result['status']}")
    if "procurement" in sxos_result:
        print(f"Action: {sxos_result['action']}")

def main():
    print("🏛️ NEXUS ASI — Sovereign Hybrid Construction & Interior Intelligence")
    print("Hybrid Pipeline: BIM + Smart Wizard + SXOS")

    # Omadhoo Standard
    run_demo("OMADHOO PRIME (Hybrid Structural/Interior)", "1500 sqft, 30x50, 3 floors, 5 hotel rooms each floor, terrace")

    # Magicplan Scan Demo
    print("\n--- 📱 MAGICPLAN AR SCAN SIMULATION ---")
    scan_data = scan_room_ar("12x15 bedroom")
    print(f"Scanned Room: {scan_data['width']}x{scan_data['depth']} {scan_data['type']}")

if __name__ == "__main__":
    main()
