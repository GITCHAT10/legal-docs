import json
from mnos.modules.finance.fce import FCEEngine
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.modules.imoxon.policies.engine import IdentityPolicyEngine
from mnos.shared.execution_guard import ExecutionGuard, _sovereign_context
from mnos.modules.imoxon.core.engine import ImoxonCore
from mnos.modules.education.engine import EducationEngine

def verify_pivot():
    print("--- UHA: Verifying 30/70 Pivot & QR Flow ---")

    # Setup
    shadow = ShadowLedger()
    events = DistributedEventBus()
    identity = AegisIdentityCore(shadow, events)
    guard = ExecutionGuard(identity, IdentityPolicyEngine(identity), FCEEngine(), shadow, events)
    imoxon = ImoxonCore(guard, FCEEngine(), shadow, events)
    education = EducationEngine(imoxon)

    sys_actor = {"identity_id": "SYSTEM", "device_id": "CORE-SRV", "role": "admin", "system_override": True}
    token = _sovereign_context.set({"token": "VERIFY-PIVOT", "actor": sys_actor})

    try:
        # 1. Create Elite Candidate
        trainee_id = identity.create_profile({"full_name": "Elite Candidate", "profile_type": "staff"})
        identity.bind_device(trainee_id, {"fingerprint": "UCO-ELITE-X"})

        # 2. Ingest Swiss School Transcript (30% weight)
        print("\n[Action] Ingesting SHL Luzern Transcript...")
        transcript = {
            "student_id": trainee_id,
            "partner_code": "SHL-LUZERN",
            "courses": [
                {"code": "SHL-MGMT-101", "grade": 5.8, "max_grade": 6.0},
                {"code": "SHL-OPS-202", "grade": 5.5, "max_grade": 6.0}
            ]
        }
        education.process_transcript(sys_actor, transcript)

        # 3. Submit Practical Assessment (70% weight)
        education.create_course(sys_actor, {"course_id": "BC-EXAM-01", "title": "Black Coral Practical", "level": "BC-3"})
        enrollment = education.enroll(sys_actor, {"course_id": "BC-EXAM-01", "student_id": trainee_id})

        print("\n[Action] Submitting Practical Assessment (90%)...")
        actor_ctx = {"identity_id": trainee_id, "device_id": "UCO-ELITE-X", "role": "staff"}
        credential = education.submit_assessment(actor_ctx, {
            "enrollment_id": enrollment["enrollment_id"],
            "score": 90
        })

        # 4. Verify QR Dashboard Data
        cred_id = [k for k in education.credentials.keys()][0]
        print(f"\n[Action] Recruiter Scanning QR for Credential: {cred_id}")
        dashboard = education.get_verification_dashboard_data(cred_id)

        print(f"Candidate Name: {dashboard['identity_handshake']['name']}")
        print(f"Academic Baseline (30%): {dashboard['snapshot_of_excellence']['academic_baseline']}%")
        print(f"Total BCSI Score: {dashboard['snapshot_of_excellence']['total_bcsi']}")
        print(f"Final Tier: {dashboard['snapshot_of_excellence']['tier']}")
        print(f"Clean Record: {dashboard['red_flag_history']['clean_record']}")
        print(f"Legal Shield: {dashboard['legal_shield'][:50]}...")

    finally:
        _sovereign_context.set(None)

if __name__ == "__main__":
    verify_pivot()
