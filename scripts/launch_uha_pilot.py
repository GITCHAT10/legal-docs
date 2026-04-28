import json
from mnos.modules.finance.fce import FCEEngine
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.modules.imoxon.policies.engine import IdentityPolicyEngine
from mnos.shared.execution_guard import ExecutionGuard, _sovereign_context
from mnos.modules.imoxon.core.engine import ImoxonCore
from mnos.modules.education.funnel import UHAQualificationFunnel
from mnos.modules.exmail.service import EXMAILAutomationService
from mnos.modules.education.urgency import UrgencyPressureEngine

def launch_pilot():
    print("--- UHA & EXMAIL: Self-Funding Flywheel Launch Simulation ---")

    # Setup
    shadow = ShadowLedger()
    events = DistributedEventBus()
    identity = AegisIdentityCore(shadow, events)
    guard = ExecutionGuard(identity, IdentityPolicyEngine(identity), FCEEngine(), shadow, events)
    imoxon = ImoxonCore(guard, FCEEngine(), shadow, events)

    funnel = UHAQualificationFunnel(imoxon)
    exmail = EXMAILAutomationService(imoxon)
    urgency = UrgencyPressureEngine()

    sys_actor = {"identity_id": "SYSTEM", "device_id": "CORE-SRV", "role": "admin", "system_override": True}
    token = _sovereign_context.set({"token": "FLYWHEEL-SIM", "actor": sys_actor})

    try:
        # 1. Talent Acquisition (UHA Funnel)
        print("\n[Step 1] UHA: Capturing lead from Meta Ads...")
        lead = funnel.capture_lead("student@hospitality.com", source="meta_ads")
        print(f"Lead Captured: {lead['lead_id']} | Intent Score: {lead['intent_score']}")

        print("[Step 1] UHA: Student watches Masterclass and completes Quiz...")
        funnel.record_engagement(lead["lead_id"], "video_watch_100")
        funnel.record_engagement(lead["lead_id"], "quiz_completed")

        lead = funnel.leads[lead["lead_id"]]
        print(f"Lead Qualified! New Intent Score: {lead['intent_score']} | Stage: {lead['stage']}")

        offer = funnel.get_offer(lead["lead_id"])
        print(f"Personalized Offer: {offer['offer']} | CTA: {offer['cta']}")

        # 2. Urgency Drive
        urgency_signals = urgency.get_urgency_payload("uha_accelerator")
        print(f"\n[Step 2] UHA: Triggering Urgency Engine...")
        print(f"Signal: {urgency_signals['countdown_text']} | {urgency_signals['remaining']}")

        # 3. Demand Generation (EXMAIL)
        print("\n[Step 3] EXMAIL: Triggering abandoned booking recovery for GCC segment...")
        seq = exmail.trigger_sequence("guest-789", "abandoned_booking", "GCC")
        print(f"Email Queued: {seq['id']} | Psychology: {seq['offer']['psychology']} | Incentive: {seq['offer']['incentive']}")

        print("[Step 3] EXMAIL: Dispatching and Auditing to SHADOW...")
        dispatched = exmail.process_queue()
        for d in dispatched:
            print(f"Dispatch Success! Audit anchored in SHADOW.")

    finally:
        _sovereign_context.set(None)

    print("\n--- Simulation Complete: Flywheel Operational ---")

if __name__ == "__main__":
    launch_pilot()
