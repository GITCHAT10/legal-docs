from fastapi import FastAPI
from skyfarm.database import engine, Base, SessionLocal
import skyfarm.identity.models
import skyfarm.marine.models
import skyfarm.agri.models
import skyfarm.logistics.models
import skyfarm.finance.models
import skyfarm.trace.models
import skyfarm.restaurant.models
import skyfarm.retail.models
import skyfarm.integration.models
import threading
from skyfarm.integration.outbox_worker import process_outbox
import time

# Create tables
Base.metadata.create_all(bind=engine)

from skyfarm.marine.router import router as marine_router
from skyfarm.agri.router import router as agri_router
from skyfarm.logistics.router import router as logistics_router
from skyfarm.finance.router import router as finance_router
from skyfarm.trace.router import router as trace_router
from skyfarm.restaurant.router import router as restaurant_router
from skyfarm.retail.router import router as retail_router
from skyfarm.integration.router import router as integration_router

app = FastAPI(title="SKYFARM API Gateway")

app.include_router(marine_router)
app.include_router(agri_router)
app.include_router(logistics_router)
app.include_router(finance_router)
app.include_router(trace_router)
app.include_router(restaurant_router)
app.include_router(retail_router)
app.include_router(integration_router)

# Background Worker Thread
def start_worker():
    while True:
        db = SessionLocal()
        try:
            process_outbox(db)
        except Exception as e:
            print(f"Worker Error: {e}")
        finally:
            db.close()
        time.sleep(5) # Poll every 5 seconds for simulation

@app.on_event("startup")
async def startup_event():
    thread = threading.Thread(target=start_worker, daemon=True)
    thread.start()

@app.get("/")
def read_root():
    return {"message": "SKYFARM API Gateway is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
