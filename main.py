import os
from fastapi import FastAPI, HTTPException, Header, Depends, Query, Request
from pydantic import BaseModel
from typing import List, Optional, Dict
from decimal import Decimal

# MNOS Core
from mnos.modules.aegis.verifier import AegisVerifier
from mnos.modules.finance.fce import FCEEngine
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import EventBus
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.modules.imoxon.policies.engine import IdentityPolicyEngine
from mnos.shared.execution_guard import ExecutionGuardMiddleware
from mnos.api.aegis_identity import create_identity_router

# iMOXON Adapters
from mnos.modules.imoxon.adapters.aegis_adapter import AegisAdapter
from mnos.modules.imoxon.adapters.fce_adapter import FCEAdapter
from mnos.modules.imoxon.adapters.shadow_adapter import ShadowAdapter
from mnos.modules.imoxon.adapters.event_adapter import EventAdapter

# iMOXON Supply Engines
from mnos.modules.imoxon.engines.demand.engine import DemandEngine
from mnos.modules.imoxon.engines.procurement.engine import ProcurementEngine
from mnos.modules.imoxon.engines.skygodown.engine import SkygodownEngine
from mnos.modules.imoxon.engines.delivery.engine import DeliveryEngine
from mnos.modules.imoxon.engines.apollo.engine import ApolloOrchestrator

app = FastAPI(title="iMOXON Supply Execution Platform")

# --- System Law (Initialization) ---
os.environ["NEXGEN_SECRET"] = os.environ.get("NEXGEN_SECRET", "mnos-supply-sovereign")
aegis_core = AegisVerifier()
fce_core = FCEEngine()
shadow_core = ShadowLedger()
events_core = EventBus()
identity_core = AegisIdentityCore(shadow_core, events_core)
policy_engine = IdentityPolicyEngine(identity_core)

app.add_middleware(ExecutionGuardMiddleware, identity_core=identity_core, policy_engine=policy_engine, events=events_core)
app.include_router(create_identity_router(identity_core, policy_engine))

aegis = AegisAdapter(aegis_core)
fce = FCEAdapter(fce_core)
shadow = ShadowAdapter(shadow_core)
events = EventAdapter(events_core)

# Engines
demand = DemandEngine(shadow, events)
procurement = ProcurementEngine(shadow, events)
skygodown = SkygodownEngine(shadow, events)
delivery = DeliveryEngine(shadow, events)
apollo = ApolloOrchestrator(shadow, events)

# --- Supply API Layer ---

@app.post("/supply/demand/signals")
async def capture_demand(resort_id: str, items: List[dict], urgency: str = "NORMAL"):
    signal = demand.capture_signal(resort_id, items, urgency)
    return {"status": "success", "signal": signal}

@app.post("/supply/rfps/award")
async def award_rfp(rfp_id: str, supplier_id: str):
    # apollo validates transition
    apollo.validate_transition("OPEN", "AWARDED")
    award = procurement.award_rfp(rfp_id, supplier_id)
    # trigger milestone via apollo
    release = apollo.trigger_milestone_payout(fce_core, "AWARD", {"total_amount": 100000})
    return {"status": "success", "award": award, "payout": release}

@app.post("/supply/lots/allocate")
async def allocate_lot(lot_id: str, resort_id: str, quantities: dict):
    allocation = skygodown.allocate_to_resort(lot_id, resort_id, quantities)
    return {"status": "success", "allocation": allocation}

@app.post("/supply/manifests/confirm")
async def confirm_delivery(manifest_id: str, resort_id: str, items: List[dict]):
    confirmation = delivery.confirm_resort_receipt(manifest_id, resort_id, items)
    # trigger final milestone
    release = apollo.trigger_milestone_payout(fce_core, "ACCEPTANCE", {"total_amount": 100000})
    return {"status": "success", "confirmation": confirmation, "payout": release}

@app.get("/health")
async def health():
    return {"status": "online", "integrity": shadow.verify_chain()}
