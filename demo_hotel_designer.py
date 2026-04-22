import json
from mnos.core.ai.parser import parse_prompt_to_request, BuildingRequest, Plot
from mnos.modules.arcos.manager import ArcoManager

# Mock MNOS Infrastructure
class MockBus:
    def emit(self, event, data):
        print(f"📡 [EVENT] {event}")
class MockShadow:
    def log(self, event, data):
        print(f"📜 [SHADOW] {event}")

def run_arcos_demo():
    print("🏛️ NEXUS ASI — ARCOs Construction Operating System")

    bus, shadow = MockBus(), MockShadow()
    arcos = ArcoManager(bus, shadow)

    # 1. Valid Omadhoo Spec
    print("\n--- [CASE 1: OMADHOO PRIME VALIDATED DESIGN] ---")
    prompt = "1500 sqft, 30x50, 3 floors, 5 hotel rooms each floor, terrace"
    request = parse_prompt_to_request(prompt)
    result = arcos.execute_build_pipeline(request)

    if result["status"] == "SUCCESS":
        print(f"✅ Build Authorized: Trace ID {result['trace_id']}")
        print(f"   FAR Result: {result['compliance']['far_result']}")
        print(f"   Steel Tons: {result['boq']['quantities']['steel_tons']}")
        print(f"   INN Inventory: {len(result['layout']['inn_inventory'])} rooms")

    # 2. FAR Failure
    print("\n--- [CASE 2: FAR VIOLATION (Too many floors)] ---")
    far_fail_request = parse_prompt_to_request(prompt)
    far_fail_request.floors = 15 # Over density
    result = arcos.execute_build_pipeline(far_fail_request)
    if result["status"] == "REJECTED":
        print(f"❌ Rejected: {result['errors'][0]}")

    # 3. Geometry Failure
    print("\n--- [CASE 3: IMPOSSIBLE PLOT (Fail-Closed)] ---")
    bad_plot_request = BuildingRequest(plot=Plot(width=30, depth=15), floors=1, rooms_per_floor=1, type="hotel")
    result = arcos.execute_build_pipeline(bad_plot_request)
    if result["status"] == "REJECTED":
        print(f"❌ Rejected: {result['errors'][0]}")

    print("\n--- ✅ ARCOs PIPELINE COMPLETE ---")

if __name__ == "__main__":
    run_arcos_demo()
