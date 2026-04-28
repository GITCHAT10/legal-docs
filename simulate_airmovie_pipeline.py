import json
import hashlib
from decimal import Decimal
from mnos.modules.finance.fce import FCEEngine
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.modules.imoxon.policies.engine import IdentityPolicyEngine
from mnos.shared.execution_guard import ExecutionGuard, _sovereign_context
from mnos.modules.imoxon.core.engine import ImoxonCore
from mnos.modules.education.engine import EducationEngine
from mnos.modules.education.content import AirMovieContentManager
from mnos.modules.education.compliance import ComplianceTriggerEngine

def simulate_pipeline():
    print("--- AIRMOVIE Pipeline & Compliance Trigger Simulation ---")

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
    airmovie = AirMovieContentManager(imoxon)
    compliance = ComplianceTriggerEngine(imoxon, education)

    # SYSTEM CONTEXT WITH DEVICE
    sys_actor = {"identity_id": "SYSTEM", "device_id": "CORE-SRV", "role": "admin", "system_override": True}
    token = _sovereign_context.set({"token": "PIPELINE-SIM-TOKEN", "actor": sys_actor})

    try:
        # 1. Publish AIRMOVIE Module (v1.0)
        print("\n[Action] Publishing AIRMOVIE Service DNA v1.0...")
        module = airmovie.publish_module(sys_actor, {
            "module_id": "SOP-DNA-001",
            "version": "1.0.0",
            "title": "Maldives Hospitality 101",
            "video_url": "https://cdn.mnos/sop/dna-001.mp4",
            "quiz_triggers": [{"timestamp": 30, "quiz_id": "Q-001"}],
            "sha256_hash": "HASH-V1"
        })
        print(f"Published: {module['module_id']} v{module['version']}")

        # 2. Get Playback Manifest for EDGE
        manifest = airmovie.get_playback_manifest("SOP-DNA-001", lang="en")
        print(f"\n[Manifest] Playback URL: {manifest['stream_url']}")
        print(f"Interactive Points: {manifest['interactive_points']}")

        # 3. Simulate Operational Failure -> Retraining Trigger
        staff_id = identity.create_profile({"full_name": "Test Staff", "profile_type": "staff"})
        print(f"\n[Action] Operational Event: HACCP Violation for staff {staff_id}")

        # We need to register the refresh course first
        education.create_course(sys_actor, {
            "course_id": "L1-HACCP-REFRESH",
            "title": "HACCP Safety Refresh",
            "modules": ["SOP-HACCP-001"]
        })

        trigger_res = compliance.handle_operational_event(
            "haccp.violation",
            staff_id,
            {"description": "Temp log missing for Batch A-102"}
        )
        print(f"Retraining Assigned: {trigger_res['required_module']} (Urgency: {trigger_res['urgency']})")

        # 4. Verify SHADOW Context
        proof = shadow.export_audit_proof()
        last_block = proof["evidence"][-1]
        print(f"\n[Audit] Last SHADOW Block type: {last_block['event_type']}")
        print(f"Authorized By: {last_block['audit_context']['authorized_by']}")
        print(f"Trace ID: {last_block['audit_context']['trace_id']}")

    finally:
        _sovereign_context.reset(token)

    print("\n--- Simulation Complete ---")

if __name__ == "__main__":
    simulate_pipeline()
