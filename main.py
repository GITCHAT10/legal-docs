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

# iMOXON Engines (All Branded)
from mnos.modules.imoxon.engines.commerce.engine import CommerceEngine
from mnos.modules.imoxon.engines.transport.engine import TransportEngine
from mnos.modules.imoxon.engines.logistics.engine import LogisticsEngine
from mnos.modules.imoxon.engines.health.engine import HealthEngine
from mnos.modules.imoxon.engines.fitness.engine import FitnessEngine
from mnos.modules.imoxon.engines.care_services.engine import CareServicesEngine
from mnos.modules.imoxon.engines.life.engine import LifeEngine
from mnos.modules.imoxon.engines.communication.engine import CommunicationEngine
from mnos.modules.imoxon.engines.pet.engine import PetEngine
from mnos.modules.imoxon.engines.creator.engine import CreatorEngine
from mnos.modules.imoxon.engines.faith.engine import FaithEngine
from mnos.modules.imoxon.engines.education.engine import EducationEngine
from mnos.modules.imoxon.engines.franchise.engine import FranchiseEngine
from mnos.modules.imoxon.engines.geo.engine import GeoEngine
from mnos.modules.imoxon.engines.affiliate.engine import AffiliateEngine
from mnos.modules.imoxon.engines.installment.engine import InstallmentEngine
from mnos.modules.imoxon.engines.rent.engine import RentEngine
from mnos.modules.imoxon.engines.escrow.engine import EscrowEngine
from mnos.modules.imoxon.engines.billpay.engine import BillPayEngine
from mnos.modules.imoxon.engines.legal.engine import LegalEngine
from mnos.modules.imoxon.engines.enforcement.engine import EnforcementEngine
from mnos.modules.imoxon.engines.maldives_rails.engine import MaldivesRailsIntegration
from mnos.modules.isky_hms.connector import iSkyCloudHMSConnector

app = FastAPI(title="iMOXON Sovereign System")
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- System Law (Authorities) ---
os.environ["NEXGEN_SECRET"] = os.environ.get("NEXGEN_SECRET", "mnos-sovereign-prod")
aegis_core = AegisVerifier()
fce_core = FCEEngine()
shadow_core = ShadowLedger()
events_core = EventBus()

aegis = AegisAdapter(aegis_core)
fce = FCEAdapter(fce_core)
shadow = ShadowAdapter(shadow_core)
events = EventAdapter(events_core)

# --- Engines Initialization ---
geo = GeoEngine()
homes = RentEngine(fce, shadow, events)
escrow = EscrowEngine(shadow, events)
pay = BillPayEngine(fce, shadow, events)
lex = LegalEngine(shadow, events)
enforcement = EnforcementEngine(shadow, events)
rails = MaldivesRailsIntegration(shadow)
market = CommerceEngine(fce, shadow, events)
move = TransportEngine(aegis, fce, shadow, events)
ship = LogisticsEngine(shadow, events, geo)
health = HealthEngine(shadow, events)
fit = FitnessEngine(shadow, events)
care = CareServicesEngine(shadow, events)
life = LifeEngine(shadow)
connect = CommunicationEngine(shadow, events)
pet = PetEngine(shadow, events)
studio = CreatorEngine(shadow, events)
deen = FaithEngine(shadow, events)
learn = EducationEngine(fce, shadow, events)
hub = FranchiseEngine(fce, shadow)
link = AffiliateEngine(fce, shadow)
flex = InstallmentEngine(fce, shadow, events)
isky = iSkyCloudHMSConnector(fce, shadow, events)

# --- AEGIS DOME Middleware ---
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

# --- API Layer (Full iMOXON Suite) ---

@app.post("/auth/onboard")
async def onboard(name: str, role: str, device_id: str):
    did = aegis.register_actor({"name": name}, role)
    aegis_core.bind_device(did, device_id)
    payload = {"did": did, "name": name, "role": role, "device": device_id}
    shadow.record_action("actor.onboarded", payload)
    events.trigger("USER_VERIFIED", payload)
    return {"status": "success", "did": did}

@app.post("/homes/tenancy", dependencies=DOME)
async def create_tenancy(landlord: str, tenant: str, rent: float):
    # Rule: Use HOMES engine for tenancy Act compliance
    return {"status": "success", "tenancy": homes.create_tenancy(landlord, tenant, "prop-1", rent, rent)}

@app.post("/pay/bill", dependencies=DOME)
async def pay_bill(user_id: str, biller: str, acct: str):
    bill = pay.fetch_bill(biller, acct)
    return {"status": "success", "payment": pay.pay_bill(user_id, bill)}

@app.post("/lex/lease", dependencies=DOME)
async def sign_lease(landlord: str, tenant: str, prop: str):
    valid, msg = rails.validate_tenancy_act_compliance(1000, 2000)
    if not valid: raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "lease": lex.generate_lease_agreement(landlord, tenant, prop, {"rent": 1000})}

@app.post("/move/ride", dependencies=DOME)
async def request_ride(user: str, dev: str, role: str, src: str, dst: str):
    return {"status": "success", "ride": move.request_ride(user, dev, role, src, dst)}

@app.post("/market/order", dependencies=DOME)
async def place_order(user: str, list_id: str, vendor: str, amt: float):
    return {"status": "success", "order": market.process_order(user, list_id, vendor, amt)}

@app.post("/isky/activate")
async def activate_isky(operator: str):
    return {"status": "success", "activation": isky.activate_hms(operator)}

@app.get("/health")
async def health():
    return {"status": "online", "shadow_integrity": shadow.verify_chain()}
