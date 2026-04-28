import json
import hashlib
import contextvars
from decimal import Decimal
from mnos.modules.finance.fce import FCEEngine
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.modules.imoxon.policies.engine import IdentityPolicyEngine
from mnos.shared.execution_guard import ExecutionGuard, _sovereign_context
from mnos.modules.imoxon.core.engine import ImoxonCore
from mnos.modules.education.engine import EducationEngine
from mnos.modules.education.pms_adapters.roomraccoon import RoomRaccoonAdapter
from mnos.modules.shadow.black_coral_protocol import BlackCoralVerificationEngine

def simulate_black_coral():
    print("--- UHA BLACK CORAL STANDARD SIMULATION ---")

    # Setup Core MNOS
    fce = FCEEngine()
    shadow = ShadowLedger()
    events = DistributedEventBus()
    identity = AegisIdentityCore(shadow, events)
    policy = IdentityPolicyEngine(identity)
    guard = ExecutionGuard(identity, policy, fce, shadow, events)
    imoxon = ImoxonCore(guard, fce, shadow, events)

    # Setup Academy
    education = EducationEngine(imoxon)
    pms_adapter = RoomRaccoonAdapter(imoxon, education)
    bcvp_engine = BlackCoralVerificationEngine(imoxon)

    # SYSTEM CONTEXT FOR SETUP
    sys_actor = {"identity_id": "SYSTEM", "device_id": "CORE-SRV", "role": "admin", "system_override": True}
    token = _sovereign_context.set({"token": "UHA-SIM-TOKEN", "actor": sys_actor})

    try:
        # 1. Create Staff Profile
        staff_id = identity.create_profile({"full_name": "Ibrahim Ahmed", "profile_type": "staff"})
        identity.bind_device(staff_id, {"fingerprint": "SALA-TAB-01"})

        # 2. Setup Luxury Training Module & Retention Strategy
        education.create_course(sys_actor, {
            "course_id": "L2-LUXURY-PROTOCOL",
            "title": "Black Coral: Luxury Service Protocol",
            "level": "BC-2"
        })
        education.create_course(sys_actor, {
            "course_id": "L3-RETENTION-STRATEGY",
            "title": "Black Coral: Guest Retention Strategy",
            "level": "BC-3"
        })
        print(f"UHA Courses Registered.")

        # 3. Simulate RoomRaccoon Webhook (VIP Reservation)
        print("\n[Action] RoomRaccoon Webhook: VIP Reservation for Platinum Guest (10 nights)...")
        pms_adapter.handle_pms_webhook("reservation.created", {
            "resort_id": "MVR_MLE_2026",
            "guest_tier": "PLATINUM",
            "nights": 10,
            "assigned_staff_id": staff_id,
            "guest_id": "GUEST-VIP-777"
        })

        # 4. Verify Auto-Enrollment
        print(f"Checking enrollment for staff {staff_id}...")
        staff_enrollments = sorted(
            [e for e in education.enrollments.values() if e["student_id"] == staff_id],
            key=lambda x: x["course_id"]
        )
        print(f"Staff enrolled in {len(staff_enrollments)} courses.")
        for e in staff_enrollments:
            print(f" - Enrolled in: {e['course_id']}")

        # 5. Submit High-Performance Assessment for Luxury Protocol
        print("\n[Action] Submitting Assessment for L2-LUXURY-PROTOCOL (Score: 98%)...")
        actor_ctx = {"identity_id": staff_id, "device_id": "SALA-TAB-01", "role": "staff"}
        l2_enrollment = [e for e in staff_enrollments if e["course_id"] == "L2-LUXURY-PROTOCOL"][0]
        result = education.submit_assessment(actor_ctx, {
            "enrollment_id": l2_enrollment["enrollment_id"],
            "score": 98
        })

        # 6. Verify Black Coral Credential
        if "@context" in result:
            print(f"SUCCESS: Black Coral Standard Credential Issued!")
            print(f"Tier: {result['credentialSubject']['tier']}")
            print(f"Anchor Hash: {result['credentialSubject']['shadow_anchor']}")
            print(f"Signature: {result['proof']['proofValue']}")
            print(f"Competencies (Quad-Stack): {result['credentialSubject']['competencies']}")
        else:
            print(f"FAILED: {result}")

        # 7. Check SHADOW Ledger for Quad-Stack Scoring & Minting
        print("\n[Audit] Checking SHADOW Ledger for Black Coral events...")
        proof = shadow.export_audit_proof()
        bc_events = [e for e in proof["evidence"] if "education" in e["event_type"]]

        for e in bc_events:
            print(f" - [{e['event_type']}] Trace ID: {e['audit_context']['trace_id']}")

    finally:
        _sovereign_context.reset(token)

    print("\n--- Simulation Complete ---")

if __name__ == "__main__":
    simulate_black_coral()
