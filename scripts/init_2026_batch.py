import json
from mnos.modules.finance.fce import FCEEngine
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.modules.imoxon.policies.engine import IdentityPolicyEngine
from mnos.shared.execution_guard import ExecutionGuard, _sovereign_context
from mnos.modules.imoxon.core.engine import ImoxonCore
from mnos.modules.education.engine import EducationEngine

def init_2026_batch():
    print("--- UHA: Initializing 2026 Elite Batch (50 Candidates) ---")

    # Core Setup (Simulated Singleton)
    shadow = ShadowLedger()
    events = DistributedEventBus()
    identity = AegisIdentityCore(shadow, events)
    guard = ExecutionGuard(identity, IdentityPolicyEngine(identity), FCEEngine(), shadow, events)
    imoxon = ImoxonCore(guard, FCEEngine(), shadow, events)
    education = EducationEngine(imoxon)

    # SYSTEM CONTEXT
    sys_actor = {"identity_id": "SYSTEM", "device_id": "CORE-SRV", "role": "admin", "system_override": True}
    token = _sovereign_context.set({"token": "INIT-BATCH-2026", "actor": sys_actor})

    try:
        # Create Course
        education.create_course(sys_actor, {
            "course_id": "BC-101-ELITE",
            "title": "2026 Elite Hospitality Leadership",
            "level": "BC-4"
        })

        for i in range(1, 51):
            name = f"Candidate 2026-{i:03}"
            trainee_id = identity.create_profile({"full_name": name, "profile_type": "staff"})
            identity.bind_device(trainee_id, {"fingerprint": f"UCO-DEVICE-{i:03}"})

            # Auto-enroll in elite course
            education.enroll(sys_actor, {"course_id": "BC-101-ELITE", "student_id": trainee_id})

        print(f"Successfully initialized 50 candidates in UHA 2026 Elite Batch.")

    finally:
        _sovereign_context.reset(token)

if __name__ == "__main__":
    init_2026_batch()
