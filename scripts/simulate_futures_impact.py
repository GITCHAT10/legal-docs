import json
from mnos.modules.finance.fce import FCEEngine
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.modules.imoxon.policies.engine import IdentityPolicyEngine
from mnos.shared.execution_guard import ExecutionGuard, _sovereign_context
from mnos.modules.imoxon.core.engine import ImoxonCore
from mnos.modules.education.engine import EducationEngine
from mnos.modules.education.futures import BlackCoralFuturesEngine, ApplicantStatus

def simulate_impact():
    print("--- BLACK CORAL FUTURES™: Impact & Funnel Simulation ---")

    # Setup
    shadow = ShadowLedger()
    events = DistributedEventBus()
    identity = AegisIdentityCore(shadow, events)
    guard = ExecutionGuard(identity, IdentityPolicyEngine(identity), FCEEngine(), shadow, events)
    imoxon = ImoxonCore(guard, FCEEngine(), shadow, events)
    education = EducationEngine(imoxon)
    futures = BlackCoralFuturesEngine(imoxon, education)

    sys_actor = {"identity_id": "SYSTEM", "device_id": "CORE-SRV", "role": "admin", "system_override": True}
    token = _sovereign_context.set({"token": "FUTURES-SIM", "actor": sys_actor})

    try:
        # 1. Capture Underserved Applicants
        print("\n[Step 1] Capturing Applicants for Q3 Pilot...")
        applicants_data = [
            {"email": "aisha.m@atoll.mv", "age": 19, "location": "Male Atoll", "pathway": "hospitality", "pdpa_consent": True, "availability_hours": 30},
            {"email": "hussain.s@atoll.mv", "age": 22, "location": "Addu", "pathway": "hospitality", "pdpa_consent": True, "availability_hours": 40},
            {"email": "mariyam.f@atoll.mv", "age": 20, "location": "Hulhumale", "pathway": "hospitality", "pdpa_consent": True, "availability_hours": 10}
        ]

        for data in applicants_data:
            applicant = futures.submit_application(data)
            print(f"Applicant Hashed: {applicant['id_hash'][:8]}... | Score: {applicant['total_score']} | Status: {applicant['status']}")

        # 2. Record Deployment for Priority Candidate
        priority_id = [k for k, v in futures.applicants.items() if v["status"] == ApplicantStatus.PRIORITY_COHORT][0]
        print(f"\n[Step 2] Deploying Priority Candidate {priority_id[:8]}... to SALA Resort.")
        futures.record_deployment(priority_id, "SALA-NORTH-01")

        # 3. Generate Impact Report for Donor
        print("\n[Step 3] Generating Impact Metrics for Donor Review...")
        metrics = futures.get_impact_metrics()
        print(f"Total Applicants: {metrics['total_applicants']}")
        print(f"Active Deployments: {metrics['active_deployments']}")
        print(f"Impact Velocity: {metrics['impact_velocity']:.2f}")
        print(f"Sovereign Audit Check: {metrics['sovereign_verified']}")

    finally:
        _sovereign_context.set(None)

    print("\n--- Simulation Complete: Impact Engine Operational ---")

if __name__ == "__main__":
    simulate_impact()
