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
from mnos.shared.execution_guard import ExecutionGuard, ExecutionGuardMiddleware
from mnos.api.aegis_identity import create_identity_router

# iMOXON Engines
from mnos.modules.imoxon.engines.commerce.engine import CommerceEngine
from mnos.modules.imoxon.engines.delivery.engine import DeliveryEngine
from mnos.modules.imoxon.engines.apollo.engine import ApolloOrchestrator

app = FastAPI(title="iMOXON Sovereign Commerce Platform")

# --- System Law (Initialization) ---
os.environ["NEXGEN_SECRET"] = os.environ.get("NEXGEN_SECRET", "mnos-sovereign-commerce")

aegis_verifier = AegisVerifier()
fce_core = FCEEngine()
shadow_core = ShadowLedger()
events_core = EventBus()
identity_core = AegisIdentityCore(shadow_core, events_core)
policy_engine = IdentityPolicyEngine(identity_core)

# Guard is the central entrypoint
guard = ExecutionGuard(identity_core, policy_engine, fce_core, shadow_core, events_core)

# Middleware enforces Fail-Closed
app.add_middleware(ExecutionGuardMiddleware, guard=guard, events=events_core)

# Routes
app.include_router(create_identity_router(identity_core, policy_engine))

# Engines initialized with Guard
commerce = CommerceEngine(guard, fce_core, shadow_core, events_core)
delivery = DeliveryEngine(guard, shadow_core, events_core)
apollo = ApolloOrchestrator(guard, shadow_core, events_core)

# --- Dependency to extract Actor Context from Headers ---
def get_actor_ctx(
    x_aegis_identity: str = Header(None, alias="X-AEGIS-IDENTITY"),
    x_aegis_device: str = Header(None, alias="X-AEGIS-DEVICE")
):
    if not x_aegis_identity or not x_aegis_device:
        raise HTTPException(status_code=403, detail="FAIL CLOSED: Missing Actor Identity or Device")
    return {"identity_id": x_aegis_identity, "device_id": x_aegis_device, "role": "staff"}

# --- Exception Handlers ---
from fastapi.responses import JSONResponse

@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})

@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    return JSONResponse(status_code=500, content={"detail": str(exc)})

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})

# --- Sovereign Commerce API ---

@app.post("/commerce/vendors/approve")
async def approve_vendor(vendor_data: dict, actor: dict = Depends(get_actor_ctx)):
    return commerce.approve_vendor(actor, vendor_data)

@app.post("/commerce/orders/create")
async def create_order(order_data: dict, actor: dict = Depends(get_actor_ctx)):
    return commerce.create_order(actor, order_data)

@app.post("/commerce/milestones/verify")
async def verify_milestone(proof_data: dict, actor: dict = Depends(get_actor_ctx)):
    return apollo.record_milestone_proof(actor, proof_data)

@app.post("/commerce/payouts/release")
async def release_payout(milestone: str, ref_id: str, total_amount: float, actor: dict = Depends(get_actor_ctx)):
    return apollo.trigger_milestone_payout(actor, fce_core, milestone, {"ref_id": ref_id, "total_amount": total_amount})

@app.get("/health")
async def health():
    return {"status": "online", "integrity": shadow_core.verify_integrity()}
