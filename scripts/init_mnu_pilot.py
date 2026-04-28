import json
from mnos.modules.finance.fce import FCEEngine
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.modules.imoxon.policies.engine import IdentityPolicyEngine
from mnos.shared.execution_guard import ExecutionGuard, _sovereign_context
from mnos.modules.imoxon.core.engine import ImoxonCore
from mnos.modules.education.engine import EducationEngine

def init_mnu_pilot():
    print("--- MNU × UHA: Initializing National Talent Pilot (20 Students) ---")

    # Core Setup
    shadow = ShadowLedger()
    events = DistributedEventBus()
    identity = AegisIdentityCore(shadow, events)
    guard = ExecutionGuard(identity, IdentityPolicyEngine(identity), FCEEngine(), shadow, events)
    imoxon = ImoxonCore(guard, FCEEngine(), shadow, events)
    education = EducationEngine(imoxon)

    # SYSTEM CONTEXT
    sys_actor = {"identity_id": "SYSTEM", "device_id": "CORE-SRV", "role": "admin", "system_override": True}
    token = _sovereign_context.set({"token": "MNU-PILOT-2026", "actor": sys_actor})

    try:
        # 1. Register MNU Courses
        education.create_course(sys_actor, {"course_id": "MNU-HOSP101", "title": "Hospitality Ops", "level": "BC-1"})
        education.create_course(sys_actor, {"course_id": "MNU-HOSP205", "title": "Food Safety", "level": "BC-2"})

        # 2. Seed 20 Students from Addu & Malé
        locations = ["ADDU", "MLE"]
        for i in range(1, 21):
            loc = locations[i % 2]
            name = f"MNU Trainee {loc}-{i:02}"
            student_id = identity.create_profile({"full_name": name, "profile_type": "staff", "assigned_island": loc})
            identity.bind_device(student_id, {"fingerprint": f"MNU-EDGE-{loc}-{i:02}"})

            # Simulate MNU Transcript Ingestion
            education.process_mnu_transcript(sys_actor, student_id, [
                {"course_code": "MNU-HOSP101", "grade": 3.8, "max_grade": 4.0},
                {"course_code": "MNU-HOSP205", "grade": 3.5, "max_grade": 4.0}
            ])

            # Auto-enroll in UHA Verification tracks
            education.enroll(sys_actor, {"course_id": "MNU-HOSP205", "student_id": student_id})

        print(f"Successfully initialized 20 MNU students for Addu/Malé pilot.")

    finally:
        _sovereign_context.reset(token)

if __name__ == "__main__":
    init_mnu_pilot()
