import json
from mnos.modules.finance.fce import FCEEngine
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.modules.imoxon.policies.engine import IdentityPolicyEngine
from mnos.shared.execution_guard import ExecutionGuard, _sovereign_context
from mnos.modules.imoxon.core.engine import ImoxonCore
from mnos.modules.education.engine import EducationEngine

def verify_national_pipeline():
    print("--- MNU × UHA: Verifying National Talent Pipeline ---")

    # Setup
    shadow = ShadowLedger()
    events = DistributedEventBus()
    identity = AegisIdentityCore(shadow, events)
    guard = ExecutionGuard(identity, IdentityPolicyEngine(identity), FCEEngine(), shadow, events)
    imoxon = ImoxonCore(guard, FCEEngine(), shadow, events)
    education = EducationEngine(imoxon)

    sys_actor = {"identity_id": "SYSTEM", "device_id": "CORE-SRV", "role": "admin", "system_override": True}
    token = _sovereign_context.set({"token": "VERIFY-NATIONAL", "actor": sys_actor})

    try:
        # 1. Create MNU Student from Addu
        print("\n[Step 1] Creating MNU Student from Addu...")
        student_id = identity.create_profile({"full_name": "Mariyam Hassan", "profile_type": "staff", "assigned_island": "ADDU"})
        identity.bind_device(student_id, {"fingerprint": "MNU-ADDU-X"})

        # 2. Ingest MNU Transcript
        print("[Step 2] Ingesting MNU Hospitality Transcript...")
        # Use direct process_mnu_transcript to ensure it hits engine state
        education.process_mnu_transcript(sys_actor, student_id, [
            {"course_code": "MNU-HOSP101", "grade": 3.9, "max_grade": 4.0},
            {"course_code": "MNU-HOSP205", "grade": 3.7, "max_grade": 4.0}
        ])

        # 3. Complete Practical Verification
        education.create_course(sys_actor, {"course_id": "MNU-HOSP205", "title": "Food Safety", "level": "BC-2"})
        enrollment = education.enroll(sys_actor, {"course_id": "MNU-HOSP205", "student_id": student_id})

        print("[Step 3] Submitting Practical Assessment (95%)...")
        actor_ctx = {"identity_id": student_id, "device_id": "MNU-ADDU-X", "role": "staff"}
        uco = education.submit_assessment(actor_ctx, {
            "enrollment_id": enrollment["enrollment_id"],
            "score": 95
        })

        # 4. Verify National UCO Data
        print(f"\n[Step 4] Verifying National UCO Issued: {uco['credential_id']}")
        print(f"Atoll Origin: {uco['atoll_origin']}")
        print(f"BCSI Final: {uco['bcsi_total']}")
        print(f"Ministry Endorsed: {uco['ministry_endorsed']}")

        # 5. Check Dashboard Data for Recruiter
        dashboard = education.get_verification_dashboard_data(uco["credential_id"])
        print(f"\n[Step 5] Recruiter Dashboard Preview:")
        print(f"Name: {dashboard['identity_handshake']['name']}")
        print(f"MIG ID: {dashboard['identity_handshake']['mig_id']}")
        print(f"Academic (MNU): {dashboard['snapshot_of_excellence']['academic_baseline']}%")
        print(f"Total BCSI: {dashboard['snapshot_of_excellence']['total_bcsi']}")

    finally:
        _sovereign_context.set(None)

if __name__ == "__main__":
    verify_national_pipeline()
