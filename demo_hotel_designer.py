import json
from mnos.core.ai.parser import parse_prompt_to_request, BuildingRequest, Plot
from mnos.modules.compliance.checker import check_maldives_compliance
from mnos.modules.layout.generator import generate_layout
from mnos.modules.finance.boq import calculate_boq_and_cost
from mnos.modules.orchestrate.asana_adapter import auto_generate_asana_board

# Mock MNOS Infrastructure
class MockBus:
    def emit(self, event, data):
        print(f"📡 [EVENT BUS] {event}: {data}")
class MockShadow:
    def log(self, event, data): pass

def run_hardened_demo():
    print("🏛️ NEXUS ASI — Sovereign Hardened Intelligence (ABEOS v2)")

    bus, shadow = MockBus(), MockShadow()

    # 1. DESIGN PIPELINE (HARDENED)
    prompt = "1500 sqft, 30x50, 3 floors, 5 hotel rooms each floor, terrace"
    request = parse_prompt_to_request(prompt)
    compliance = check_maldives_compliance(request)
    layout = generate_layout(request, compliance)

    # BOQ with Event Emission
    boq = calculate_boq_and_cost(layout, event_bus=bus)

    print(f"\n[🏗️ ABEOS DESIGN] Omadhoo Project Validated.")
    print(f"INN Inventory: {len(layout['inn_inventory'])} Rooms Generated.")
    print(f"FCE Ledger: Total Commitment {boq['fce_ledger']['total_commitment']} USD")

    # 2. FAIL FAST DEMO
    print("\n[⚠️ FAIL-FAST DEMO - Small Plot 30x15]")
    bad_request = BuildingRequest(plot=Plot(width=30, depth=15), floors=1, rooms_per_floor=1, type="hotel")
    bad_layout = generate_layout(bad_request, check_maldives_compliance(bad_request))
    print(f"Status: {bad_layout.get('status')} | Reason: {bad_layout.get('error')}")

    # 3. ASANA HANDOVER
    asana_board = auto_generate_asana_board(layout, boq)
    print(f"\n[📋 ASANA HANDOVER] Board Created: {asana_board['board_name']}")
    for task in asana_board['tasks']:
        print(f" - {task['name']}")

    print("\n--- ✅ HARDENING COMPLETE ---")

if __name__ == "__main__":
    run_hardened_demo()
