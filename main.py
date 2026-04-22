import os
from fastapi import FastAPI, HTTPException, Header, Depends, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict
from decimal import Decimal
import logging

# MNOS Core
from mnos.core.eleone import EleoneEngine
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
from mnos.modules.imoxon.engines.commerce.engine import CommerceEngine
from mnos.modules.imoxon.engines.franchise.engine import FranchiseEngine
from mnos.modules.imoxon.engines.geo.engine import GeoEngine
from mnos.modules.imoxon.engines.affiliate.engine import AffiliateEngine
from mnos.modules.imoxon.engines.food.engine import FoodEngine
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
from mnos.modules.imoxon.engines.installment.engine import InstallmentEngine
from mnos.modules.isky_hms.connector import iSkyCloudHMSConnector

app = FastAPI(title="iMOXON Sovereign Local Economy Engine")

app.mount("/static", StaticFiles(directory="static"), name="static")

# --- System Law (Initialization) ---
os.environ["NEXGEN_SECRET"] = os.environ.get("NEXGEN_SECRET", "mnos-sovereign-2024")

# Authorities
aegis_core = AegisVerifier()
fce_core = FCEEngine()
shadow_core = ShadowLedger()
events_core = EventBus()

# Adapters
aegis = AegisAdapter(aegis_core)
fce = FCEAdapter(fce_core)
shadow = ShadowAdapter(shadow_core)
events = EventAdapter(events_core)

# Idempotency Cache
idempotency_cache = {}

# Engines
engines = {
    "commerce": CommerceEngine(shadow, events),
    "franchise": FranchiseEngine(fce, shadow),
    "geo": GeoEngine(),
    "affiliate": AffiliateEngine(fce, shadow),
    "food": FoodEngine(None, fce, shadow, events),
    "transport": TransportEngine(aegis, fce, shadow, events),
    "logistics": LogisticsEngine(shadow, events, None),
    "health": HealthEngine(shadow, events),
    "fitness": FitnessEngine(shadow, events),
    "care": CareServicesEngine(shadow, events),
    "life": LifeEngine(shadow),
    "comm": CommunicationEngine(shadow, events),
    "pet": PetEngine(shadow, events),
    "creator": CreatorEngine(shadow, events),
    "faith": FaithEngine(shadow, events),
    "education": EducationEngine(fce, shadow, events),
    "installment": InstallmentEngine(fce, shadow, events),
    "isky": iSkyCloudHMSConnector(fce, shadow, events)
}

# --- Schemas ---
class OnboardRequest(BaseModel):
    name: str
    role: str
    device_id: Optional[str] = None

class RideRequest(BaseModel):
    user_id: str
    device_id: str
    role: str
    pickup: str
    destination: str

# --- API Layer ---

def check_idempotency(key: str):
    if key and key in idempotency_cache: return idempotency_cache[key]
    return None

@app.post("/auth/onboard")
async def onboard(data: OnboardRequest, idempotency_key: Optional[str] = Header(None)):
    if cached := check_idempotency(idempotency_key): return cached
    try:
        did = aegis.register_actor(data.dict(), data.role)
        if data.device_id: aegis_core.bind_device(did, data.device_id)
        payload = {"did": did, **data.dict()}
        shadow.record_action("actor.onboarded", payload)
        events.trigger("USER_VERIFIED", payload)
        res = {"status": "success", "did": did}
        if idempotency_key: idempotency_cache[idempotency_key] = res
        return res
    except PermissionError as e: raise HTTPException(status_code=403, detail=str(e))
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))

@app.post("/transport/ride")
async def request_ride(data: RideRequest, idempotency_key: Optional[str] = Header(None)):
    if cached := check_idempotency(idempotency_key): return cached
    ride = engines["transport"].request_ride(data.user_id, data.device_id, data.role, data.pickup, data.destination)
    # SALA 2026: Add simulated carbon footprint for the ride
    ride["carbon_footprint_kg"] = 2.5
    res = {"status": "success", "ride": ride}
    if idempotency_key: idempotency_cache[idempotency_key] = res
    return res

@app.post("/market/listing")
async def create_listing(vendor_id: str, title: str, price: float, carbon_footprint_kg: float = 0.0):
    engines["commerce"].create_listing(vendor_id, {
        "title": title,
        "price": price,
        "carbon_footprint_kg": carbon_footprint_kg
    })
    return {"status": "success"}

@app.post("/isky/activate")
async def activate_hms(operator_id: str):
    activation = engines["isky"].activate_hms(operator_id)
    return {"status": "success", "activation": activation}

@app.get("/health")
async def health():
    return {"status": "online", "shadow_integrity": shadow.verify_chain()}
