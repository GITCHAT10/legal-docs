from fastapi import FastAPI
from contextlib import asynccontextmanager
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
import skyfarm.chefs_farm.models
import threading
from skyfarm.integration.outbox_worker import process_outbox
from skyfarm.integration.logging_utils import logger
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
from skyfarm.chefs_farm.router import router as chefs_farm_router

# Background Worker Thread
def start_worker():
    logger.info("Outbox worker thread starting")
    while True:
        db = SessionLocal()
        try:
            process_outbox(db)
        except Exception as e:
            logger.error(f"Worker Error: {e}")
        finally:
            db.close()
        time.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    thread = threading.Thread(target=start_worker, daemon=True)
    thread.start()
    logger.info("SKYFARM application started")
    yield

app = FastAPI(title="SKYFARM + SXOS Economic Node", lifespan=lifespan)

app.include_router(marine_router)
app.include_router(agri_router)
app.include_router(logistics_router)
app.include_router(finance_router)
app.include_router(trace_router)
app.include_router(restaurant_router)
app.include_router(retail_router)
app.include_router(integration_router)
app.include_router(chefs_farm_router)

@app.get("/")
def read_root():
    return {"message": "SKYFARM + SXOS Economic Node is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
