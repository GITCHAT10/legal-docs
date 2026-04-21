import json
from mnos.core.ai.parser import parse_prompt_to_request
from mnos.modules.compliance.checker import check_maldives_compliance
from mnos.modules.layout.generator import generate_layout
from mnos.modules.finance.boq import calculate_boq_and_cost

def main():
    print("--- 🧠 AI Hotel Designer for Maldives ---")

    # 1. User Prompt
    prompt = "1500 sqft, 30x50, 3 floors, 5 hotel rooms each floor, terrace"
    print(f"\n[1] User Prompt: \"{prompt}\"")

    # 2. AI Parser
    request = parse_prompt_to_request(prompt)
    print("\n[2] Parsed Request (JSON):")
    print(json.dumps(request.model_dump(), indent=2))

    # 3. Compliance Check
    compliance = check_maldives_compliance(request)
    print("\n[3] Maldives Compliance Check:")
    print(f"    Status: {'✅ COMPLIANT' if compliance['is_compliant'] else '❌ NON-COMPLIANT'}")
    for rec in compliance['recommendations']:
        print(f"    Recommendation: {rec}")
    for viol in compliance['violations']:
        print(f"    Violation: {viol}")

    # 4. Layout Generation
    layout = generate_layout(request, compliance)
    print("\n[4] Concept Layout Generated:")
    print(f"    Components count: {len(layout['components'])}")
    # Print only first 3 components for brevity
    for comp in layout['components'][:3]:
        print(f"    - {comp['type'].capitalize()}: {comp.get('dimensions', 'N/A')}")

    # 5. BOQ + Cost Estimation
    cost_data = calculate_boq_and_cost(layout)
    print("\n[5] BOQ + Cost Estimate (Maldives Rates):")
    print(f"    Total Estimated Area: {cost_data['quantities']['total_area_sqm']} sqm")
    print(f"    Concrete: {cost_data['quantities']['concrete_m3']} m3")
    print(f"    Steel: {cost_data['quantities']['steel_tons']} tons")
    print(f"\n    Estimated Total Cost: {cost_data['currency']} {cost_data['total_estimate']:,}")
    print("    (Includes 35% Labor and 15% Island Transport markup)")

    print("\n--- ✅ End of Demo ---")

if __name__ == "__main__":
    main()
