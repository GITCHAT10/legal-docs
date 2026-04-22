import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal

# Import MNOS Modules
from mnos.core.eleone import EleoneEngine
from mnos.modules.aegis.verifier import AegisVerifier
from mnos.modules.finance.fce import FCEEngine
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.events.bus import EventBus

# Import iMOXON Modules
from imoxon.marketplace import MarketplaceEngine
from imoxon.merchant import MerchantEngine
from imoxon.supply import SupplyEngine
from imoxon.tourism import TourismEngine
from imoxon.exchange import ExchangeEngine

app = FastAPI(title="iMOXON Commerce & Exchange Layer")

app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Core Engines (Singleton-like for demo)
# Ensure NEXGEN_SECRET is set for Aegis
os.environ["NEXGEN_SECRET"] = os.environ.get("NEXGEN_SECRET", "mnos-default-secret-2024")

aegis = AegisVerifier()
fce = FCEEngine()
shadow = ShadowLedger()
events = EventBus()
eleone = EleoneEngine()

marketplace = MarketplaceEngine()
merchant = MerchantEngine()
supply = SupplyEngine(events)
tourism = TourismEngine(fce)
exchange = ExchangeEngine(shadow, events)

# Pydantic Schemas
class UserOnboard(BaseModel):
    name: str
    email: str

class MerchantOnboard(BaseModel):
    business_name: str
    registration_number: str
    bank_account: str

class ListingCreate(BaseModel):
    title: str
    category: str # retail, tourism, asset
    price: float
    stock: int
    merchant_id: str

class CheckoutRequest(BaseModel):
    user_token: str
    listing_id: str
    coupon_code: Optional[str] = None

class InstallmentRequest(BaseModel):
    total: float
    months: int

class TourismBookingRequest(BaseModel):
    user_token: str
    experience_type: str
    pax: int
    nights: int
    base_price_per_pax: float

class AssetListRequest(BaseModel):
    merchant_id: str
    asset_name: str
    price: float

class AssetTransferRequest(BaseModel):
    asset_id: str
    buyer_token: str
    amount: float

# --- Onboarding Endpoints ---

@app.post("/onboard/user")
async def onboard_user(data: UserOnboard):
    did = aegis.create_did({"name": data.name, "email": data.email})
    payload = {"did": did, "name": data.name, "email": data.email}
    shadow.commit("imoxon.user.onboarded", payload)
    events.publish("imoxon.user.onboarded", payload)
    return {"status": "success", "did": did, "token": f"mnos-tok-{did[:8]}"}

@app.post("/onboard/merchant")
async def onboard_merchant(data: MerchantOnboard):
    if not aegis.verify_kyb(data.dict()):
        raise HTTPException(status_code=400, detail="KYB Verification Failed")

    did = aegis.create_did(data.dict())
    payload = {"did": did, **data.dict()}
    shadow.commit("imoxon.merchant.onboarded", payload)
    events.publish("imoxon.merchant.onboarded", payload)
    return {"status": "success", "did": did, "dashboard_unlocked": True}

# --- Listing Endpoints ---

@app.post("/listings")
async def create_listing(data: ListingCreate):
    listing_id = f"lst_{hash(data.title) % 10000}"
    details = data.dict()
    details["listing_id"] = listing_id

    marketplace.add_listing(listing_id, details)
    merchant.update_stock(listing_id, data.stock)

    shadow.commit("imoxon.listing.created", details)
    events.publish("imoxon.listing.created", details)

    return {"status": "success", "listing_id": listing_id}

@app.get("/listings")
async def get_listings():
    return marketplace.get_listings()

@app.get("/events/history")
async def get_event_history():
    return events.get_history()

@app.get("/health")
async def health():
    return {"status": "online", "integrity": shadow.verify_integrity()}

# --- Commerce Endpoints (Phase B) ---

@app.post("/checkout")
async def checkout(data: CheckoutRequest):
    # Rule 1: Fail Closed
    if not aegis.verify_identity(data.user_token):
        raise HTTPException(status_code=401, detail="Invalid Identity Token")

    lst = marketplace.get_listings().get(data.listing_id)
    if not lst:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Check inventory
    if not merchant.decrement_stock(data.listing_id, 1):
        raise HTTPException(status_code=400, detail="Out of stock")

    base_price = Decimal(str(lst["price"]))
    is_tourism = lst["category"] == "tourism"

    # Apply coupon if any
    discount = 0.0
    if data.coupon_code:
        discount_pct = marketplace.validate_coupon(data.coupon_code)
        if discount_pct > 0:
            discount = float(base_price) * (discount_pct / 100.0)
            base_price -= Decimal(str(discount))

    pricing = fce.calculate_order_total(base_price, is_tourism=is_tourism)

    order = {
        "user_token": data.user_token,
        "listing_id": data.listing_id,
        "pricing": pricing,
        "discount": discount,
        "status": "PAID"
    }

    # Immutable record
    shadow.commit("imoxon.order.completed", order)

    # Orchestration
    events.publish("imoxon.order.completed", order)

    return {"status": "success", "order": order}

@app.post("/installments")
async def create_installments(data: InstallmentRequest):
    schedule = fce.calculate_installments(Decimal(str(data.total)), data.months)
    return {"status": "success", "schedule": schedule}

# --- Operation Endpoints (Tourism, Supply, Exchange) ---

@app.post("/tourism/book")
async def book_tourism(data: TourismBookingRequest):
    if not aegis.verify_identity(data.user_token):
        raise HTTPException(status_code=401, detail="Invalid Identity Token")

    booking = tourism.book_experience(
        data.user_token,
        data.experience_type,
        data.pax,
        data.nights,
        data.base_price_per_pax
    )

    shadow.commit("imoxon.tourism.booked", booking)
    events.publish("imoxon.tourism.booked", booking)
    return {"status": "success", "booking": booking}

@app.post("/supply/restock")
async def restock(merchant_id: str, listing_id: str, amount: int):
    # FCE could approve B2B here
    result = supply.trigger_restock(merchant_id, listing_id, amount)
    shadow.commit("imoxon.supply.triggered", result)
    return {"status": "success", "supply_event": result}

@app.post("/assets/list")
async def list_asset(data: AssetListRequest):
    listing = exchange.list_asset(data.merchant_id, data.asset_name, data.price)
    return {"status": "success", "asset": listing}

@app.post("/assets/transfer")
async def transfer_asset(data: AssetTransferRequest):
    if not aegis.verify_identity(data.buyer_token):
        raise HTTPException(status_code=401, detail="Invalid Identity Token")

    exchange.initiate_transfer(data.asset_id, data.buyer_token, data.amount)
    # Simulate immediate finalization for demo
    exchange.finalize_transfer(data.asset_id)

    return {"status": "success", "transfer_finalized": True}

@app.post("/payout")
async def process_payout(merchant_id: str, amount: float):
    # FCE calculates net payout (simplified)
    tax_withheld = amount * 0.05
    net = amount - tax_withheld

    payout = {
        "merchant_id": merchant_id,
        "gross": amount,
        "tax_withheld": tax_withheld,
        "net": net,
        "timestamp": "now"
    }
    shadow.commit("imoxon.payout.processed", payout)
    events.publish("imoxon.payout.processed", payout)
    return {"status": "success", "payout": payout}
