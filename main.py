import os
from fastapi import FastAPI, HTTPException, Header, Depends, Query, Request, Body
from fastapi.responses import JSONResponse
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

# U-Series Verticals
from mnos.modules.u_hotel.engine import UHotelEngine
from mnos.modules.u_marine.engine import UMarineEngine
from mnos.modules.u_fb.engine import MaldivesRestaurantEngine as UFBEngine
from mnos.modules.u_laundry.engine import MaldivesLaundryEngine as ULaundryEngine

# Mocks/Legacy for compatibility
from mnos.modules.finance.escrow import EscrowFCETCore
from mnos.modules.imoxon.procurement.engine import ProcurementEngine

app = FastAPI(title="UPOS Cloud: Universal Commerce Nervous System")

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
    if x_aegis_session:
        return identity_gateway.validate_session(x_aegis_session)

    if not x_aegis_identity:
        raise HTTPException(status_code=401, detail="AEGIS_REQUIRED")

    profile = identity_core.profiles.get(x_aegis_identity)
    return {
        "identity_id": x_aegis_identity,
        "device_id": x_aegis_device,
        "role": profile.get("profile_type") if profile else "guest",
        "verified": profile.get("verification_status") == "verified" if profile else False
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

# --- U-Enterprise / MAC EOS Governance ---

@app.get("/upos/enterprise/dashboard")
async def enterprise_dashboard(actor: dict = Depends(get_actor_ctx)):
    """
    U-Enterprise: Master Command Dashboard.
    Reports Live Revenue, Cost, GOP, and Risk.
    """
    # In a real system, these would be aggregated from FCE/SHADOW
    return {
        "status": "OPERATIONAL",
        "governance": "MAC EOS / MNOS",
        "metrics": {
            "live_revenue_mvr": 1250000.0,
            "live_cost_mvr": 450000.0,
            "live_gop_mvr": 800000.0,
            "active_vouchers": 1240,
            "u_wifi_routers_online": len(u_wifi.routers),
            "active_wifi_sessions": len(u_wifi.active_sessions)
        },
        "risk_alerts": [],
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

@app.get("/health")
async def health():
    return {"status": "online", "foundation": "SALA Node / UPOS Cloud", "version": "v1.0.0"}
