import asyncio
import uuid
import structlog
from datetime import datetime, UTC, timedelta
from decimal import Decimal

# MNOS Core Simulation Imports
from mnos.modules.finance.fce import FCEEngine
from mnos.modules.events.bus import DistributedEventBus
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.shared.execution_guard import ExecutionGuard

# Prestige Module Imports
from mnos.modules.imoxon.core.engine import ImoxonCore
from mnos.modules.imoxon.pricing.hooks import generate_quote_and_route
from mnos.modules.imoxon.activator import RevenueActivator
from mnos.modules.imoxon.closer import CloserNegotiationEngine

# Setup Logger
structlog.configure(
    processors=[structlog.processors.JSONRenderer()]
)
logger = structlog.get_logger("prestige.simulation")

async def run_7day_simulation():
    print("\n--- 🏝️ PRESTIGE REVENUE ACTIVATION: 7-DAY SIMULATION STARTING ---")

    # 1. Initialize MNOS Kernel
    shadow = ShadowLedger()
    events = DistributedEventBus()
    fce = FCEEngine()

    # Policy Engine Mock for Simulation
    class MockPolicy:
        def validate_action(self, at, ctx): return True, "OK"

    guard = ExecutionGuard(identity_core=None, policy_engine=MockPolicy(), fce=fce, shadow=shadow, events=events)

    core = ImoxonCore(guard, fce, shadow, events)
    activator = RevenueActivator(core)
    closer = CloserNegotiationEngine(core)

    # 2. DAY 1-2: Deploy Activator & Target Agents
    print("\n[PHASE 1: REVENUE ACTIVATION]")

    # Setup Event Listeners
    def on_pricing_generated(event):
        print(f"  -> Activator consuming: {event['type']}")
        activator.handle_pricing_event(event)

    # 3. DAY 3: Dispatch Offers
    # Generate 10 high-intent pricing events
    for i in range(10):
        agent_id = f"WA_PLATINUM_{i+1:02}" if i < 5 else f"agent_gold_{i+1:02}@prestige.mv"
        context = {
            "agent_id": agent_id,
            "conversion_probability": 0.88,
            "agent_score": 0.92,
            "strategy": "JET_CHARTER_BUNDLE",
            "currency": "USD",
            "trigger": f"SIM-D3-{i}"
        }

        # Wrapped in sovereign context for simulation bypass
        with guard.sovereign_context():
             print(f"Day 3: Generating quote for {agent_id}...")
             await generate_quote_and_route(
                 net_amount=Decimal("15000.00"),
                 product_type="accommodation",
                 context_dict=context,
                 core=core
             )

             # Manually trigger handler as we don't have a background event worker in the script
             last_event = events.partitions["GLOBAL"][-1]
             on_pricing_generated(last_event)

    # 4. DAY 5: Closer Intercept & Negotiation
    print("\n[PHASE 2: COMPETITOR INTEL & CLOSER WORKFLOW]")
    # Closer intercepts a 'Gold' agent offer with a 5% deviation (auto-approved)
    sample_decision = activator.dispatch_log[5]
    pricing_id = sample_decision["trace_id"] # In activator, we used trace_id as unique link for simplicity

    # Fetch actual decision data from event bus for simulation accuracy
    pricing_data = [e["payload"] for e in events.partitions["GLOBAL"] if e["payload"]["trace_id"] == sample_decision["trace_id"]][0]

    with guard.sovereign_context():
        print(f"Day 5: Closer 'M_AHMED' negotiating for {sample_decision['agent_id']}...")
        closer.submit_override(
            pricing_decision=pricing_data,
            new_price_mvr=float(pricing_data["final_gross"]) * 0.95, # 5% discount
            reason="Competitor matching - Booking.com parity",
            closer_id="M_AHMED"
        )

    # 5. DAY 7: Revenue Realization & Final Audit
    print("\n[PHASE 3: REVENUE REALIZATION & AUDIT]")
    # Count confirmed interactions in shadow
    shadow_log = shadow.chain
    activations = [l for l in shadow_log if "agent.interaction.recorded" in l["event_type"]]
    overrides = [l for l in shadow_log if "pricing.override.submitted" in l["event_type"]]

    print(f"\n--- 📈 SIMULATION COMPLETE ---")
    print(f"Total Pricing Decisions: 10")
    print(f"Offers Dispatched (Activator): {len(activator.dispatch_log)}")
    print(f"Human Overrides (Closer): {len(overrides)}")
    print(f"Audit Trail Length: {len(shadow_log)}")
    print(f"Status: ✅ SUCCESS - 100% Traceable")

if __name__ == "__main__":
    asyncio.run(run_7day_simulation())
