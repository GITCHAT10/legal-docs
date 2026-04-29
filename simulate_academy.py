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
from mnos.modules.education.sync import AcademySyncEngine

def simulate_academy():
    print("--- MARS Academy Academy Simulation ---")

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
    sync_engine = AcademySyncEngine(imoxon, education)

    # AUTHORIZE SYSTEM OPERATIONS (Bypass SHADOW restriction for setup)
    _sovereign_context.set({"token": "SIM-SYSTEM-TOKEN", "actor": {"identity_id": "SYSTEM", "role": "admin"}})

    try:
        # 1. Create Actor (Staff Member)
        staff_id = identity.create_profile({
            "full_name": "Ahmed Sameer",
            "profile_type": "staff",
            "assigned_island": "SALA-01"
        })
        device_id = identity.bind_device(staff_id, {"fingerprint": "MARS-EDGE-001"})

        actor_ctx = {
            "identity_id": staff_id,
            "device_id": device_id,
            "role": "staff",
            "island": "SALA-01"
        }

        # 2. Create Course (Admin Action)
        print("\n[Action] Creating L1 Service DNA Course...")
        course = education.create_course(actor_ctx, {
            "title": "L1: Service DNA & Island Hospitality",
            "level": "L1",
            "modules": ["Orientation", "15/5 Rule", "Anticipatory Care"]
        })
        print(f"Course Created: {course['course_id']} - {course['title']}")

        # 3. Enroll Staff
        print(f"\n[Action] Enrolling Staff {staff_id} in Course...")
        enrollment = education.enroll(actor_ctx, {"course_id": course["course_id"]})
        print(f"Enrolled: {enrollment['enrollment_id']} - Status: {enrollment['status']}")

        # 4. Submit Assessment (Simulating Passing Grade)
        print("\n[Action] Submitting Assessment (Score: 95%)...")
        result = education.submit_assessment(actor_ctx, {
            "enrollment_id": enrollment["enrollment_id"],
            "score": 95
        })

        if "certificate_id" in result:
            print(f"SUCCESS: Certificate Issued! ID: {result['certificate_id']}")
            print(f"Forensic Hash: {result['forensic_hash']}")
        else:
            print(f"FAILED: Score {result['score']}% did not pass.")

        # 5. Verify Certificate
        print("\n[Action] Verifying Certificate...")
        verification = education.verify_certificate(result["certificate_id"])
        print(f"Verification Status: {verification['status']}")

        # 6. Verify SHADOW Ledger
        print("\n[Audit] Checking SHADOW Ledger for Forensic Proof...")
        proof = shadow.export_audit_proof()
        edu_events = [e for e in proof["evidence"] if "education" in e["event_type"]]

        print(f"Found {len(edu_events)} education-related forensic events in SHADOW.")
        for e in edu_events:
            print(f" - [{e['event_type']}] Actor: {e['actor_id']} - Status: {e['payload'].get('status') or 'OK'}")

        # 7. Simulate EDGE Sync
        print("\n[Action] Simulating EDGE Offline Sync...")
        offline_event_data = {
            "enrollment_id": enrollment["enrollment_id"],
            "score": 88
        }
        offline_event_hash = hashlib.sha256(json.dumps(offline_event_data, sort_keys=True).encode()).hexdigest()

        sync_batch = [{
            "id": "EVT-001",
            "action_type": "education.assessment.submit",
            "actor_ctx": actor_ctx,
            "timestamp": "2024-05-20T10:00:00Z",
            "data": offline_event_data,
            "hash": offline_event_hash
        }]

        sync_results = sync_engine.process_edge_sync("EDGE-SALA-01", sync_batch)
        print(f"Sync Results: {sync_results}")

    finally:
        _sovereign_context.set(None)

    print("\n--- Simulation Complete ---")

if __name__ == "__main__":
    simulate_academy()
