import os
from fastapi import FastAPI, HTTPException, Header, Depends, Query, Request
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict
from decimal import Decimal

# MNOS Core (N-DEOS)
from mnos.modules.finance.fce import FCEEngine, FCEHardenedEngine
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.modules.imoxon.policies.engine import IdentityPolicyEngine
from mnos.shared.execution_guard import ExecutionGuard, ExecutionGuardMiddleware
from mnos.api.aegis_identity import create_identity_router
from mnos.api.commerce import create_commerce_router
from mnos.api.finance import create_finance_router
from mnos.api.specialized import create_specialized_router
from mnos.gateway.engine import APIGatewayControlPlane

# iMOXON Consolidated
from mnos.modules.imoxon.core.engine import (
    ImoxonCore, CatalogManager, ProcurementEngine,
    CampaignManager, MerchantManager, POSManager
)
from mnos.modules.imoxon.resort.weekly_system import ResortWeeklyOrderSystem

# Finance RC1
from mnos.modules.finance.payment_layer import PaymentAbstractionLayer
from mnos.modules.finance.escrow import EscrowFCETCore

# Logistics Engine
from mnos.modules.imoxon.logistics.engine import LogisticsEngine
from mnos.modules.imoxon.logistics.router import create_logistics_router

# Failover Protocol
from mnos.core.failover.protocol_0200 import Protocol0200Failover

# Shared Core Authority
from mnos.core.mig_hub.authority import MIGCoreAuthority, UnitedTransferAPI, iMoxonTradeAPI

# Specialized Engines
from mnos.modules.tourism.engine import TourismEngine
from mnos.modules.faith.engine import FaithEngine
from mnos.modules.transport.engine import TransportEngine
from mnos.modules.housing.engine import HousingEngine
from mnos.modules.exchange.engine import ExchangeEngine
from mnos.modules.education.engine import EducationEngine

# Bubble OS Super App Layer
from mnos.modules.bubble.chat.engine import ChatIntentEngine, ChatToTransactionEngine
from mnos.modules.bubble.sdk.core.bridge import BubbleSDK
from mnos.modules.bubble.pos.engine import BubblePOSEngine
from mnos.modules.bubble.pos.bridge import BubbleBPEBridge

app = FastAPI(title="iMOXON N-DEOS: Consolidated Architecture Final")

# --- System Law ---
# SECURITY: Fail-closed if secret is missing in production environment.
# PRODUCTION_RC1: Hard-enforcement.
NEXGEN_SECRET = os.environ.get("NEXGEN_SECRET")
if not NEXGEN_SECRET:
    raise RuntimeError("FAIL CLOSED: NEXGEN_SECRET must be set via environment.")

# Database Initialization
from mnos.db.session import init_db
init_db()

fce_core = FCEEngine()
shadow_core = ShadowLedger()
events_core = DistributedEventBus()
identity_core = AegisIdentityCore(shadow_core, events_core)
policy_engine = IdentityPolicyEngine(identity_core)
gateway = APIGatewayControlPlane()

# Guard remains central authority
guard = ExecutionGuard(identity_core, policy_engine, fce_core, shadow_core, events_core)
fce_hardened = FCEHardenedEngine(shadow_core)

# Core Instances
imoxon = ImoxonCore(guard, fce_core, shadow_core, events_core)
imoxon.campaign_manager = CampaignManager(imoxon)
merchant = MerchantManager(imoxon)

# BUBBLE POS Engine (BPE)
bpe = BubblePOSEngine(imoxon)
bpe_bridge = BubbleBPEBridge(imoxon, bpe)

pos = POSManager(imoxon, bpe)
catalog = CatalogManager(imoxon)

# Finance RC1
payment_rails = PaymentAbstractionLayer(fce_core)
escrow_core = EscrowFCETCore(fce_core, shadow_core)

procurement = ProcurementEngine(imoxon)
# Re-instantiate Legacy Procurement for test compatibility if needed
# But use the consolidated one for RC1
resort_system = ResortWeeklyOrderSystem(procurement)

# Logistics Engine
logistics_engine = LogisticsEngine(guard, fce_core, shadow_core, events_core, identity_core, merchant)

# Failover Protocol
failover_protocol = Protocol0200Failover(guard, shadow_core, events_core)

# Shared Core Authority
mig_core = MIGCoreAuthority(shadow_core, events_core, fce_core)
ut_api = UnitedTransferAPI(mig_core)
imoxon_trade = iMoxonTradeAPI(mig_core)

# Specialized Engines
tourism = TourismEngine(imoxon)
faith = FaithEngine(imoxon)
transport = TransportEngine(imoxon)
housing = HousingEngine(imoxon)
exchange = ExchangeEngine(imoxon)
education = EducationEngine(imoxon)

# Bubble OS
intent_engine = ChatIntentEngine(imoxon)
chat_os = ChatToTransactionEngine(imoxon, intent_engine)
sdk = BubbleSDK(imoxon)

# L1 & L2 Security
@app.middleware("http")
async def gateway_middleware(request: Request, call_next):
    if request.url.path.startswith("/imoxon") or request.url.path.startswith("/bubble"):
        await gateway.enforce_policy(request)
    return await call_next(request)

app.add_middleware(ExecutionGuardMiddleware, guard=guard, events=events_core)

# --- Dependency ---
def get_actor_ctx(
    x_aegis_identity: str = Header(None, alias="X-AEGIS-IDENTITY"),
    x_aegis_device: str = Header(None, alias="X-AEGIS-DEVICE"),
    x_aegis_verified: bool = Header(False, alias="X-AEGIS-VERIFIED")
):
    if not x_aegis_identity or not x_aegis_device:
        raise HTTPException(status_code=403, detail="FAIL CLOSED: Missing Identity or Device")
    return {
        "identity_id": x_aegis_identity,
        "device_id": x_aegis_device,
        "role": "admin",
        "national_id_verified": x_aegis_verified
    }

# --- Consolidated APIs ---

@app.post("/imoxon/suppliers/connect")
async def connect_supplier(name: str, actor: dict = Depends(get_actor_ctx)):
    return imoxon.execute_commerce_action("imoxon.supplier.connect", actor, lambda: {"name": name, "status": "CONNECTED"})

@app.post("/commerce/products/import")
async def import_product(sid: str, raw: dict, actor: dict = Depends(get_actor_ctx)):
    return catalog.import_supplier_product(actor, sid, raw)

@app.post("/commerce/products/approve")
async def approve_product(pid: str, actor: dict = Depends(get_actor_ctx)):
    return catalog.approve_product(actor, pid)

@app.post("/commerce/b2b/procurement-request")
async def b2b_procure(data: dict, actor: dict = Depends(get_actor_ctx)):
    return procurement.create_b2b_request(actor, data)

@app.post("/bubble/chat/message")
async def chat_message(message: str, actor: dict = Depends(get_actor_ctx)):
    return chat_os.process_message(actor, message)

# --- Routers ---
app.include_router(create_identity_router(identity_core, policy_engine))
app.include_router(create_commerce_router(imoxon, catalog, merchant, pos, procurement, get_actor_ctx))
app.include_router(create_finance_router(fce_hardened, get_actor_ctx))
app.include_router(create_logistics_router(logistics_engine, get_actor_ctx))
app.include_router(create_specialized_router(tourism, faith, transport, housing, exchange, education, get_actor_ctx))

# Error handlers
@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})

@app.post("/system/failover/0200/activate")
async def activate_failover(actor: dict = Depends(get_actor_ctx)):
    failover_protocol.activate_protocol_0200()
    return {"status": "FAILOVER_PROTOCOL_0200_ACTIVE"}

@app.post("/system/failover/0200/recover")
async def recover_failover(actor: dict = Depends(get_actor_ctx)):
    failover_protocol.start_recovery()
    return {"status": "RECOVERY_COMPLETE"}

@app.get("/health")
async def health():
    return {
        "status": "online",
        "integrity": shadow_core.verify_integrity(),
        "version": "CONSOLIDATED-RC1",
        "failover_mode": failover_protocol.mode.value
    }
