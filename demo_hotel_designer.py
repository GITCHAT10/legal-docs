import json
from mnos.core.ai.parser import parse_prompt_to_request, BuildingRequest, Plot
from mnos.modules.compliance.checker import check_maldives_compliance
from mnos.modules.layout.generator import generate_layout
from mnos.modules.finance.boq import calculate_boq_and_cost
from mnos.modules.finance.sxos_adapter import release_sxos_wave_2
from mnos.modules.interior.designer import scan_room_ar
from mnos.modules.orchestrate.engine import generate_island_timeline
from mnos.modules.orchestrate.asana_adapter import auto_generate_asana_board

def run_demo(label, prompt_or_request, island="Male'"):
    print(f"\n--- {label} ---")
    if isinstance(prompt_or_request, str):
        print(f"Prompt: \"{prompt_or_request}\"")
        request = parse_prompt_to_request(prompt_or_request)
    else:
        request = prompt_or_request

    # 1. Compliance
    compliance = check_maldives_compliance(request)
    if not compliance['is_compliant']:
        print(f"Compliance: ❌ FAIL")
        return

    # 2. Geometry + Interiors
    layout = generate_layout(request, compliance)
    if "error" in layout:
        print(f"Engine Error: ❌ {layout['error']}")
        return

    # 3. BOQ
    boq = calculate_boq_and_cost(layout)

    # 4. ORCHESTRATION (Asana-Style Timeline)
    complexity = (request.floors * 0.5) + (request.rooms_per_floor * 0.1)
    timeline = generate_island_timeline(island, complexity)

    # 5. ASANA WORKFLOW ENGINE (NEW: Human coordination layer)
    asana_board = auto_generate_asana_board(layout, boq)
    print(f"\n[📋 ASANA BOARD - {asana_board['board_name']}]")
    print(f"Human Layer Status: {asana_board['human_layer_status']}")
    print("Actionable Tasks (Auto-generated from ABEOS):")
    # Show first task from each phase
    phases_shown = set()
    for t in asana_board['tasks']:
        if t['phase'] not in phases_shown:
            print(f" - [{t['phase']}] {t['name']} (Assigned: {t['role']})")
            phases_shown.add(t['phase'])

    # 6. Consolidated Economics
    print(f"\n[📊 CONSOLIDATED BOQ]")
    print(f"Steel: {boq['quantities']['steel_tons']} Tons | Furniture: ${boq['costs']['furniture']:,}")
    print(f"Total Estimate: {boq['currency']} {boq['total_estimate']:,}")

    # 7. SXOS Trigger (Automated Supply Chain)
    print("\n[🚀 SXOS WAVE 2 TRIGGER]")
    sxos_result = release_sxos_wave_2(boq)
    print(f"Status: {sxos_result['status']}")

def main():
    print("🏛️ NEXUS ASI — Sovereign Construction & Orchestration Intelligence")
    print("Hybrid Autonomous + Human Pipeline: ABEOS + ASANA")

    # Omadhoo Standard
    run_demo("OMADHOO PRIME (Design-to-Deployment)",
             "1500 sqft, 30x50, 3 floors, 5 hotel rooms each floor, terrace",
             island="Omadhoo")

if __name__ == "__main__":
    main()
