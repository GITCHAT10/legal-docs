import os
from fastapi import FastAPI, HTTPException, Header, Depends, Query, Request
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict
from decimal import Decimal

# MNOS Core
from mnos.modules.finance.fce import FCEEngine
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import EventBus
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.modules.imoxon.policies.engine import IdentityPolicyEngine
from mnos.shared.execution_guard import ExecutionGuard, ExecutionGuardMiddleware
from mnos.api.aegis_identity import create_identity_router

# iMOXON Consolidated
from mnos.modules.imoxon.core.engine import ImoxonCore, SupplierManager, CatalogManager, PricingEngine, OrderManager

app = FastAPI(title="iMOXON Consolidated Commerce Platform - RC1")

# --- System Law ---
os.environ["NEXGEN_SECRET"] = os.environ.get("NEXGEN_SECRET", "imoxon-rc1-sovereign")

fce_core = FCEEngine()
shadow_core = ShadowLedger()
events_core = EventBus()
identity_core = AegisIdentityCore(shadow_core, events_core)
policy_engine = IdentityPolicyEngine(identity_core)

guard = ExecutionGuard(identity_core, policy_engine, fce_core, shadow_core, events_core)
app.add_middleware(ExecutionGuardMiddleware, guard=guard, events=events_core)

# Core Instance
imoxon = ImoxonCore(guard, fce_core, shadow_core, events_core)
suppliers = SupplierManager(imoxon)
catalog = CatalogManager(imoxon)
pricing = PricingEngine(imoxon)
orders = OrderManager(imoxon)

# --- Dependency ---
def get_actor_ctx(
    x_aegis_identity: str = Header(None, alias="X-AEGIS-IDENTITY"),
    x_aegis_device: str = Header(None, alias="X-AEGIS-DEVICE")
):
    if not x_aegis_identity or not x_aegis_device:
        raise HTTPException(status_code=403, detail="FAIL CLOSED: Missing Identity or Device")
    return {"identity_id": x_aegis_identity, "device_id": x_aegis_device, "role": "admin"}

# --- Consolidated APIs ---

@app.post("/imoxon/suppliers/connect")
async def connect_supplier(data: dict, actor: dict = Depends(get_actor_ctx)):
    return suppliers.connect_supplier(actor, data)

@app.post("/imoxon/products/import")
async def import_products(sid: str, items: List[dict], actor: dict = Depends(get_actor_ctx)):
    return catalog.import_products(actor, sid, items)

@app.post("/imoxon/products/approve")
async def approve_product(pid: str, actor: dict = Depends(get_actor_ctx)):
    return catalog.approve_product(actor, pid)

@app.get("/imoxon/catalog")
async def get_catalog():
    return catalog.catalog

@app.post("/imoxon/pricing/landed-cost")
async def calc_landed(base: float, cat: str = "RESORT_SUPPLY", actor: dict = Depends(get_actor_ctx)):
    return pricing.calculate_landed_cost(actor, base, cat)

@app.post("/imoxon/orders/create")
async def create_order(data: dict, actor: dict = Depends(get_actor_ctx)):
    return orders.create_order(actor, data)

# Error handlers
@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})

@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    return JSONResponse(status_code=500, content={"detail": str(exc)})

app.include_router(create_identity_router(identity_core, policy_engine))

@app.get("/health")
async def health():
    return {"status": "online", "integrity": shadow_core.verify_integrity()}
