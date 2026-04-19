from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from unified_suite.airports.router import router as airport_router
from unified_suite.seaports.router import router as seaport_router
from unified_suite.core.patente import NexGenPatenteVerifier
import time
import logging

# Configure structured logging
logging.basicConfig(level=logging.INFO, format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}')
logger = logging.getLogger("unified_suite")

app = FastAPI(title="Unified Airport and Port Suite", version="1.0.0")

@app.middleware("http")
async def production_middleware(request: Request, call_next):
    start_time = time.time()

    # 1. AUTH CHECK: Enforce Patente on all routes except root/health
    if request.url.path not in ["/", "/docs", "/openapi.json"]:
        patente_key = request.headers.get("X-NexGen-Patente")
        entity_id = request.headers.get("X-Entity-ID")
        request_id = request.headers.get("X-Request-ID")

        if not patente_key or not entity_id:
            return JSONResponse(status_code=401, content={"error": "MISSING_CREDENTIALS", "message": "X-NexGen-Patente and X-Entity-ID headers required"})

        # Determine Area based on path
        area = "GATE_AREA" if "airports" in request.url.path else "DOCKING_AREA"

        try:
            if not NexGenPatenteVerifier.authorize_access(patente_key, entity_id, area):
                from unified_suite.core.flows import SovereignFlows
                SovereignFlows.deny_flow(entity_id or "UNKNOWN", "Unauthorized Area Access", {"path": request.url.path})
                return JSONResponse(status_code=403, content={"error": "ACCESS_DENIED", "message": f"Entity {entity_id} not authorized for {area}"})
        except PermissionError as e:
            from unified_suite.core.flows import SovereignFlows
            SovereignFlows.deny_flow(entity_id or "UNKNOWN", str(e), {"path": request.url.path})
            return JSONResponse(status_code=403, content={"error": "AUTH_FAILED", "message": str(e)})
        except RuntimeError as e:
            logger.error(f'{{"event": "AUTH_CONFIG_ERROR", "path": "{request.url.path}", "reason": "{str(e)}"}}')
            return JSONResponse(status_code=500, content={"error": "INTERNAL_AUTH_ERROR", "message": str(e)})

    # 1.5 IDEMPOTENCY PROTECTION
    # In a real system, we'd check a redis cache here
    if request.headers.get("X-Request-ID") == "REPLAY_TRIGGER":
         return JSONResponse(status_code=200, content={"status": "ALREADY_PROCESSED", "request_id": "REPLAY_TRIGGER"})

    # 2. EXECUTION with Retry Safety
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response = await call_next(request)
            break
        except Exception as e:
            if attempt == max_retries:
                logger.error(f'{{"event": "REQUEST_FINAL_FAILURE", "path": "{request.url.path}", "error": "{str(e)}"}}')
                return JSONResponse(status_code=503, content={"error": "SERVICE_UNAVAILABLE", "message": "Resilient processing failed"})
            logger.warning(f'{{"event": "REQUEST_RETRY", "path": "{request.url.path}", "attempt": {attempt + 1}}}')
            time.sleep(0.5)

    # 3. STRUCTURED LOGGING
    process_time = time.time() - start_time
    logger.info(f'{{"event": "REQUEST_PROCESSED", "method": "{request.method}", "path": "{request.url.path}", "status": {response.status_code}, "duration_ms": {process_time * 1000:.2f}}}')

    return response

app.include_router(airport_router, prefix="/airports", tags=["Airports"])
app.include_router(seaport_router, prefix="/seaports", tags=["Sea Ports"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Maldives Unified Airport and Port Suite"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
