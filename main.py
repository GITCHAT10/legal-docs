import os
from fastapi import FastAPI, HTTPException, Header, Depends, Query, Request
from fastapi.responses import JSONResponse
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
from mnos.modules.imoxon.engines.faith.engine import FaithEngine
from mnos.modules.imoxon.engines.education.engine import EducationEngine
from mnos.modules.imoxon.engines.transport.engine import TransportEngine
from mnos.modules.imoxon.engines.rent.engine import RentEngine
from mnos.modules.imoxon.engines.escrow.engine import EscrowEngine
from mnos.modules.imoxon.engines.installment.engine import InstallmentEngine
from mnos.modules.imoxon.engines.coupon.engine import CouponEngine
from mnos.modules.imoxon.engines.tourism.engine import TourismEngine
from mnos.modules.imoxon.engines.exchange.engine import ExchangeEngine
from mnos.modules.imoxon.engines.pos.engine import POSEngine

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
faith = FaithEngine(guard, fce_core, shadow_core, events_core)
education = EducationEngine(guard, fce_core, shadow_core, events_core)
transport = TransportEngine(guard, fce_core, shadow_core, events_core)
rent = RentEngine(guard, fce_core, shadow_core, events_core)
escrow = EscrowEngine(guard, fce_core, shadow_core, events_core)
installment = InstallmentEngine(guard, fce_core, shadow_core, events_core)
coupon = CouponEngine(guard, fce_core, shadow_core, events_core)
tourism = TourismEngine(guard, fce_core, shadow_core, events_core)
exchange = ExchangeEngine(guard, fce_core, shadow_core, events_core)
pos = POSEngine(guard, fce_core, shadow_core, events_core)

# --- Dependency to extract Actor Context from Headers ---
def get_actor_ctx(
    x_aegis_identity: str = Header(None, alias="X-AEGIS-IDENTITY"),
    x_aegis_device: str = Header(None, alias="X-AEGIS-DEVICE")
):
    if not x_aegis_identity or not x_aegis_device:
        raise HTTPException(status_code=403, detail="FAIL CLOSED: Missing Actor Identity or Device")
    return {"identity_id": x_aegis_identity, "device_id": x_aegis_device, "role": "staff"}

# --- Exception Handlers ---
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

@app.post("/commerce/coupon/campaign")
async def create_coupon(data: dict, actor: dict = Depends(get_actor_ctx)):
    return coupon.create_campaign(actor, data)

@app.post("/commerce/pos/stock")
async def update_pos_stock(data: dict, actor: dict = Depends(get_actor_ctx)):
    return pos.update_stock(actor, data)

# --- Domain Engines API ---
@app.post("/faith/donate")
async def faith_donate(data: dict, actor: dict = Depends(get_actor_ctx)):
    return faith.record_donation(actor, data)

@app.post("/education/enroll")
async def edu_enroll(data: dict, actor: dict = Depends(get_actor_ctx)):
    return education.process_enrollment(actor, data)

@app.post("/transport/book")
async def transport_book(data: dict, actor: dict = Depends(get_actor_ctx)):
    return transport.book_journey(actor, data)

@app.post("/rent/lease")
async def rent_lease(data: dict, actor: dict = Depends(get_actor_ctx)):
    return rent.create_lease(actor, data)

@app.post("/finance/installment")
async def create_installment(total: float, months: int, actor: dict = Depends(get_actor_ctx)):
    return installment.create_plan(actor, total, months)

@app.post("/tourism/book")
async def tourism_book(data: dict, actor: dict = Depends(get_actor_ctx)):
    return tourism.book_package(actor, data)

@app.post("/exchange/transfer")
async def asset_transfer(data: dict, actor: dict = Depends(get_actor_ctx)):
    return exchange.transfer_asset(actor, data)

@app.get("/health")
async def health():
    return {"status": "online", "integrity": shadow_core.verify_integrity()}
