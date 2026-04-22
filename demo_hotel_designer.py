import json
from mnos.core.ai.parser import parse_prompt_to_request, BuildingRequest, Plot
from mnos.modules.compliance.checker import check_maldives_compliance
from mnos.modules.layout.generator import generate_layout
from mnos.modules.finance.boq import calculate_boq_and_cost
from mnos.modules.finance.sxos_adapter import release_sxos_wave_2
from mnos.modules.orchestrate.engine import generate_island_timeline
from mnos.modules.orchestrate.asana_adapter import auto_generate_asana_board

# Mock MNOS Infrastructure
class MockBus:
    def emit(self, event, data): pass
class MockShadow:
    def log(self, event, data): pass

from mnos.modules.iot.registry import MarsStateManager, MarsDeviceRegistry
from mnos.modules.iot.context import MarsContextEngine
from mnos.modules.iot.automation import MarsAutomationEngine
from mnos.modules.recon.core import MarsReconnaissanceCore
from mnos.modules.recon.threat import MarsSecurityEvent

def run_mars_integration_demo():
    print("🏛️ NEXUS ASI — Sovereign Hybrid Intelligence (ABEOS + MARS)")

    # 1. DESIGN PIPELINE
    prompt = "1500 sqft, 30x50, 3 floors, 5 hotel rooms each floor, terrace"
    request = parse_prompt_to_request(prompt)
    compliance = check_maldives_compliance(request)
    layout = generate_layout(request, compliance)
    boq = calculate_boq_and_cost(layout)

    print(f"\n[🏗️ ABEOS DESIGN] Omadhoo Project: {boq['quantities']['total_area_sqm']} sqm")
    print(f"Allocated {len(layout['mars_hardware'])} MARS NEXTGEN Hardware units.")
    print(f"Total Estimate: ${boq['total_estimate']:,} (Including MARS Systems)")

    # 2. MARS EXECUTION LAYER SIMULATION
    bus, shadow = MockBus(), MockShadow()
    registry = MarsDeviceRegistry(shadow)
    state_manager = MarsStateManager(bus, shadow)
    context_engine = MarsContextEngine(shadow)
    automation = MarsAutomationEngine(state_manager, context_engine)
    recon = MarsReconnaissanceCore(shadow, bus)

    # Scene: Welcome Mode
    print("\n[🤖 MARS AUTOMATION - GUEST CHECK-IN]")
    context_engine.update_context("Room_1", user_id="GUEST_007", occupancy=True)
    automation.add_rule("Welcome Home", "MARS_CHECKIN", {"user_id": "GUEST_007"}, "Room_1_LIGHT", "ON")
    automation.process_event("MARS_CHECKIN", {"location": "Room_1"})

    # Threat Correlation
    print("\n[🚨 MARS THREAT CORRELATION - INTRUSION]")
    recon.threat_engine.process_security_event(MarsSecurityEvent(event_type="MOTION_DETECTED", source_id="CAM_01", location="Lobby"))
    recon.threat_engine.process_security_event(MarsSecurityEvent(event_type="DOOR_FORCED", source_id="SENS_01", location="Lobby"))

    incident = list(recon.incident_engine.incidents.values())[0]
    print(f"Status: {incident.status} | Severity: {incident.severity} | Title: {incident.title}")

    # 3. ASANA HANDOVER
    asana_board = auto_generate_asana_board(layout, boq)
    print(f"\n[📋 ASANA HANDOVER] Board Created: {asana_board['board_name']}")
    print(f"Initial Phase Task: {asana_board['tasks'][0]['name']}")

    print("\n--- ✅ INTEGRATION COMPLETE ---")

if __name__ == "__main__":
    run_mars_integration_demo()
