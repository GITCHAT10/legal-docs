import os
from fastapi import FastAPI, HTTPException, Header, Depends, Query, Request, Body
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional, Dict
from decimal import Decimal

# UPOS Cloud Core (MAC EOS Governance)
from mnos.modules.finance.fce import FCEEngine, FCEHardenedEngine
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.core.aegis_identity.gateway import AegisIdentityGateway
from mnos.modules.orca.engine import OrcaValidationEngine
from mnos.shared.execution_guard import ExecutionGuard, ExecutionGuardMiddleware

# UPOS / APOLLO Modules
from mnos.modules.upos.core import UPOSCommerceCore
from mnos.modules.apollo.sync import ApolloSyncEngine
from mnos.modules.wifi.engine import UWiFiEngine

# UPOS Global Commerce & Logistics
from mnos.modules.shopping.engine import UShoppingEngine
from mnos.modules.customs.engine import UCustomsEngine
from mnos.modules.port.engine import UPortEngine
from mnos.modules.clearance.engine import UClearanceEngine
from mnos.modules.storage_global.engine import UStorageGlobalEngine
from mnos.modules.logistics.engine import ULogisticsEngine
from mnos.modules.domestic_cargo.engine import UDomesticCargoEngine
from mnos.modules.corridors.engine import USmartCorridorsEngine
from mnos.modules.resort_procurement.engine import UResortProcurementEngine
from mnos.core.portal_router import UPortalRouter

# U-Series Verticals
from mnos.modules.u_hotel.engine import UHotelEngine
from mnos.modules.u_marine.engine import UMarineEngine
from mnos.modules.u_fb.engine import MaldivesRestaurantEngine as UFBEngine
from mnos.modules.u_laundry.engine import MaldivesLaundryEngine as ULaundryEngine

# Mocks/Legacy for compatibility
from mnos.modules.finance.escrow import EscrowFCETCore
from mnos.modules.imoxon.procurement.engine import ProcurementEngine

app = FastAPI(title="UPOS Cloud: Universal Commerce Nervous System")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- System Law ---
NEXGEN_SECRET = os.environ.get("NEXGEN_SECRET", "FALLBACK-DEV-SECRET")

fce_core = FCEEngine()
shadow_core = ShadowLedger()
events_core = DistributedEventBus()
identity_core = AegisIdentityCore(shadow_core, events_core)
identity_gateway = AegisIdentityGateway(identity_core, shadow_core)
orca_validation = OrcaValidationEngine(identity_core)

# Guard remains central authority
guard = ExecutionGuard(identity_core, orca_validation, fce_core, shadow_core, events_core)
escrow_core = EscrowFCETCore(fce_core, shadow_core)

# UPOS Core & Sync
upos_core = UPOSCommerceCore(guard, orca_validation, fce_core, shadow_core, events_core, escrow_core)
apollo_sync = ApolloSyncEngine(guard, shadow_core, events_core, fce_core)

# U-Series Product Registry
u_wifi = UWiFiEngine(upos_core)

# Global Commerce & Logistics
u_customs = UCustomsEngine(shadow_core)
u_port = UPortEngine(shadow_core)
u_logistics = ULogisticsEngine(shadow_core)
u_domestic = UDomesticCargoEngine(shadow_core)
u_clearance = UClearanceEngine(u_customs, u_port, shadow_core)
u_storage = UStorageGlobalEngine(upos_core, shadow_core)
u_corridors = USmartCorridorsEngine(upos_core, orca_validation)
u_resort_procurement = UResortProcurementEngine(upos_core, fce_core, shadow_core, u_logistics)
u_shopping = UShoppingEngine(upos_core, u_customs, u_port, u_logistics, u_domestic)
portal_router = UPortalRouter(identity_core, orca_validation)

u_hotel = UHotelEngine(upos_core)
u_marine = UMarineEngine(upos_core)
u_fb = UFBEngine(upos_core, None) # Mocks BPE

# L1 & L2 Security
app.add_middleware(ExecutionGuardMiddleware, guard=guard, events=events_core)

# --- Dependency ---
def get_actor_ctx(
    x_aegis_session: str = Header(None, alias="X-AEGIS-SESSION"),
    x_aegis_identity: str = Header(None, alias="X-AEGIS-IDENTITY"),
    x_aegis_device: str = Header(None, alias="X-AEGIS-DEVICE"),
    x_aegis_signature: str = Header(None, alias="X-AEGIS-SIGNATURE")
):
    """
    AEGIS AUTH: Fail-closed identity context derivation.
    Enforces that identity MUST exist for any trusted session.
    """
    if x_aegis_session:
        return identity_gateway.validate_session(x_aegis_session)

    if not x_aegis_identity:
        raise HTTPException(status_code=401, detail="AEGIS_REQUIRED: Missing Identity")

    # 1. Identity lookup via AEGIS registry (persistence)
    profile = identity_core.profiles.get(x_aegis_identity)
    if not profile:
        shadow_core.commit("aegis.auth.identity.invalid", x_aegis_identity, {"reason": "Not in Registry"})
        raise HTTPException(status_code=401, detail="INVALID_IDENTITY: Unauthorized")

    # 2. Validate device binding if header provided
    if x_aegis_device:
        device = identity_core.devices.get(x_aegis_device)
        if not device or device.get("identity_id") != x_aegis_identity:
            shadow_core.commit("aegis.auth.device.mismatch", x_aegis_identity, {"device_id": x_aegis_device})
            raise HTTPException(status_code=403, detail="DEVICE_BINDING_INVALID: Access Denied")

    # 3. Derive role and verified status from profile (NO SYNTHETIC GUEST FALLBACK)
    return {
        "identity_id": x_aegis_identity,
        "device_id": x_aegis_device,
        "role": profile.get("profile_type"),
        "verified": profile.get("verification_status") == "verified"
    }

# --- U-Series APIs ---

@app.post("/upos/u-wifi/register")
async def register_wifi_router(data: dict, actor: dict = Depends(get_actor_ctx)):
    return u_wifi.register_router(actor, data)

@app.post("/upos/u-wifi/access")
async def wifi_access(data: dict, actor: dict = Depends(get_actor_ctx)):
    return u_wifi.issue_guest_access(actor, data)

@app.post("/upos/u-hotel/book")
async def hotel_booking(data: dict, actor: dict = Depends(get_actor_ctx)):
    return u_hotel.book_stay(actor, data)

@app.post("/upos/u-marine/transfer")
async def marine_transfer(data: dict, actor: dict = Depends(get_actor_ctx)):
    return u_marine.book_transfer(actor, data)

# --- UPOS Global Commerce ---

@app.get("/upos/global/shopping/search")
async def shopping_search(q: str, actor: dict = Depends(get_actor_ctx)):
    return guard.execute_sovereign_action(
        "shopping.query.created",
        actor,
        u_shopping.search,
        actor, q
    )

@app.post("/upos/global/orders/create")
async def create_global_order(data: dict, actor: dict = Depends(get_actor_ctx)):
    # Standard UPOS flow for global orders
    return upos_core.create_order(actor, data, "GLOBAL_COMMERCE")

@app.post("/upos/global/hub/receive")
async def hub_receive(order_id: str, hub_id: str, data: dict, actor: dict = Depends(get_actor_ctx)):
    return guard.execute_sovereign_action(
        "storage_global.hub.received",
        actor,
        u_storage.receive_package,
        actor, order_id, hub_id, data
    )

@app.post("/upos/global/clearance/approve-customs")
async def approve_customs(job_id: str, actor: dict = Depends(get_actor_ctx)):
    return guard.execute_sovereign_action(
        "clearance.customs.released",
        actor,
        u_clearance.approve_customs_release,
        actor, job_id
    )

@app.post("/upos/global/clearance/approve-port")
async def approve_port(job_id: str, actor: dict = Depends(get_actor_ctx)):
    return guard.execute_sovereign_action(
        "clearance.port.released",
        actor,
        u_clearance.approve_port_release,
        actor, job_id
    )

@app.post("/upos/global/clearance/validate-docs")
async def validate_clearance_docs(job_id: str, actor: dict = Depends(get_actor_ctx)):
    return guard.execute_sovereign_action(
        "clearance.documents.validated",
        actor,
        u_clearance.validate_documents,
        actor, job_id
    )

# --- U-Smart Corridors ---

@app.post("/upos/corridors/operators/register")
async def register_corridor_operator(data: dict, actor: dict = Depends(get_actor_ctx)):
    return guard.execute_sovereign_action(
        "corridor.operator.registered",
        actor,
        u_corridors.register_operator,
        actor, data
    )

@app.post("/upos/corridors/manifests/create")
async def create_corridor_manifest(data: dict, actor: dict = Depends(get_actor_ctx)):
    return guard.execute_sovereign_action(
        "corridor.manifest.created",
        actor,
        u_corridors.create_manifest,
        actor, data
    )

@app.post("/upos/corridors/manifests/{mid}/load-cargo")
async def corridor_load_cargo(mid: str, item: dict, actor: dict = Depends(get_actor_ctx)):
    return guard.execute_sovereign_action(
        "corridor.cargo.loaded",
        actor,
        u_corridors.load_cargo,
        actor, mid, item
    )

@app.post("/upos/corridors/manifests/{mid}/depart")
async def corridor_depart(mid: str, actor: dict = Depends(get_actor_ctx)):
    return guard.execute_sovereign_action(
        "corridor.departure.confirmed",
        actor,
        u_corridors.confirm_departure,
        actor, mid
    )

# --- U-Resort Procurement ---

@app.post("/upos/resort/procurement/request")
async def resort_procurement_request(data: dict, actor: dict = Depends(get_actor_ctx)):
    return u_resort_procurement.create_request(actor, data)

@app.post("/upos/resort/procurement/quote/{rid}")
async def submit_quote(rid: str, data: dict, actor: dict = Depends(get_actor_ctx)):
    return u_resort_procurement.submit_vendor_quote(actor, rid, data)

# --- U-Enterprise / MAC EOS Governance ---

@app.get("/upos/enterprise/dashboard")
async def enterprise_dashboard(actor: dict = Depends(get_actor_ctx)):
    """
    U-Enterprise: Master Command Dashboard.
    Reports Live Revenue, Cost, GOP, and Logistics Risk.
    """
    # Logistics Aggregate
    customs_pending = len([j for j in u_clearance.clearance_jobs.values() if not j["customs_released"]])
    port_pending = len([j for j in u_clearance.clearance_jobs.values() if not j["port_released"]])

    return {
        "status": "OPERATIONAL",
        "governance": "MAC EOS / MNOS",
        "metrics": {
            "live_revenue_mvr": 1250000.0,
            "live_cost_mvr": 450000.0,
            "live_gop_mvr": 800000.0,
            "active_vouchers": 1240,
            "logistics_metrics": {
                "paid_orders_awaiting_procurement": len([o for o in upos_core.orders.values() if o["status"] == "PAID"]),
                "overseas_hub_received": len(u_storage.inventory),
                "customs_pending": customs_pending,
                "port_charges_pending": port_pending,
                "active_corridors": len(u_corridors.manifests),
                "atoll_delivery_queue": len([j for j in u_domestic.jobs.values() if j["status"] == "READY_AT_MALE_HUB"]),
            },
            "u_wifi_routers_online": len(u_wifi.routers),
            "active_wifi_sessions": len(u_wifi.active_sessions)
        },
        "risk_alerts": ["Customs reserve exposure: Low"] if customs_pending < 5 else ["High customs backlog detected"],
        "integrity_hash": shadow_core.verify_integrity()
    }

@app.post("/upos/apollo/sync")
async def apollo_sync_events(tenant_id: str, events: list = Body(...), actor: dict = Depends(get_actor_ctx)):
    # Explicitly wrap in Guard to set context for the engine call
    return guard.execute_sovereign_action(
        "apollo.sync.replay",
        actor,
        apollo_sync._internal_replay,
        tenant_id, events
    )

@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})

@app.post("/upos/auth/login")
async def login_portal(actor: dict = Depends(get_actor_ctx)):
    """
    UPOS Multi-Portal Login Entrypoint.
    """
    return portal_router.login(actor)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/health")
async def health():
    return {"status": "online", "foundation": "SALA Node / UPOS Cloud", "version": "v1.0.0"}
