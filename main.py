import os
from fastapi import FastAPI, HTTPException, Header, Depends, Query, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict
from decimal import Decimal

# MNOS Core
from mnos.modules.aegis.verifier import AegisVerifier
from mnos.modules.finance.fce import FCEEngine
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import EventBus

# iMOXON Adapters
from mnos.modules.imoxon.adapters.aegis_adapter import AegisAdapter
from mnos.modules.imoxon.adapters.fce_adapter import FCEAdapter
from mnos.modules.imoxon.adapters.shadow_adapter import ShadowAdapter
from mnos.modules.imoxon.adapters.event_adapter import EventAdapter

# iMOXON Engines
from mnos.modules.imoxon.engines.rent.engine import RentEngine
from mnos.modules.imoxon.engines.escrow.engine import EscrowEngine
from mnos.modules.imoxon.engines.billpay.engine import BillPayEngine
from mnos.modules.imoxon.engines.legal.engine import LegalEngine
from mnos.modules.imoxon.engines.enforcement.engine import EnforcementEngine
from mnos.modules.imoxon.engines.maldives_rails.engine import MaldivesRailsIntegration
from mnos.modules.imoxon.engines.commerce.engine import CommerceEngine
from mnos.modules.imoxon.engines.transport.engine import TransportEngine

app = FastAPI(title="iMOXON Sovereign System")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Authorities
aegis_core = AegisVerifier()
fce_core = FCEEngine()
shadow_core = ShadowLedger()
events_core = EventBus()

aegis = AegisAdapter(aegis_core)
fce = FCEAdapter(fce_core)
shadow = ShadowAdapter(shadow_core)
events = EventAdapter(events_core)

# Engines
geo = None # Stub
homes = RentEngine(fce, shadow, events)
escrow = EscrowEngine(shadow, events)
pay = BillPayEngine(fce, shadow, events)
lex = LegalEngine(shadow, events)
enforcement = EnforcementEngine(shadow, events)
rails = MaldivesRailsIntegration(shadow)
market = CommerceEngine(fce, shadow, events)
move = TransportEngine(aegis, fce, shadow, events)

# --- AEGIS Middleware ---
async def aegis_dome_gate(request: Request):
    user_id = request.headers.get("X-MNOS-USER")
    device_id = request.headers.get("X-MNOS-DEVICE")
    role = request.headers.get("X-MNOS-ROLE", "TOURIST_USER")
    if request.url.path in ["/health", "/docs", "/openapi.json"] or request.url.path.startswith("/static") or request.url.path == "/auth/onboard":
        return
    if not user_id or not device_id:
        raise HTTPException(status_code=401, detail="AEGIS: Identity missing.")
    try:
        aegis.authorize(user_id, device_id, role)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

DOME = [Depends(aegis_dome_gate)]

# --- API ---
@app.post("/auth/onboard")
async def onboard(name: str, role: str, device_id: str):
    did = aegis.register_actor({"name": name}, role)
    aegis_core.bind_device(did, device_id)
    return {"status": "success", "did": did}

@app.post("/move/ride", dependencies=DOME)
async def request_ride(user: str, dev: str, role: str, src: str, dst: str):
    # Match frontend expectations for /transport/ride if needed, but here we provide move/ride
    return {"status": "success", "ride": move.request_ride(user, dev, role, src, dst)}

@app.post("/market/listing", dependencies=DOME)
async def create_listing(vendor: str, title: str, price: float):
    market.create_listing(vendor, {"title": title, "price": price})
    return {"status": "success"}

@app.post("/homes/tenancy", dependencies=DOME)
async def create_tenancy(landlord: str, tenant: str, rent: float):
    return {"status": "success", "tenancy": homes.create_tenancy(landlord, tenant, "prop-1", rent, rent)}

@app.post("/lex/lease", dependencies=DOME)
async def sign_lease(landlord: str, tenant: str, prop: str):
    return {"status": "success", "lease": lex.generate_lease_agreement(landlord, tenant, prop, {"rent": 1000})}

@app.post("/isky/activate")
async def activate_isky(operator: str):
    return {"status": "success", "activation": isky_hms_stub().activate_hms(operator)}

@app.get("/health")
async def health():
    return {"status": "online", "shadow_integrity": shadow.verify_chain()}

def isky_hms_stub():
    from mnos.modules.isky_hms.connector import iSkyCloudHMSConnector
    return iSkyCloudHMSConnector(fce, shadow, events)
