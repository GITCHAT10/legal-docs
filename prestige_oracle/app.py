import os
import time
from collections import defaultdict
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import Dict, List, Literal, Optional

from .scoring import predict_success
from .shadow_update import CompetencyBelief, process_shadow_event
from .deployment_matcher import evaluate_deployment
from .exmail_optimizer import optimize_exmail_offer

app = FastAPI(title="PRESTIGE ORACLE v1", version="1.0.0")

# Security
API_KEY = os.getenv("PRESTIGE_API_KEY", "staging-dev-key-CHANGE-IN-PROD")
api_key_header = APIKeyHeader(name="X-PRESTIGE-API-KEY")
rate_store = defaultdict(list)

async def verify_api(key: str = Depends(api_key_header)):
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

async def rate_limit(request: Request, key: str = Depends(verify_api)):
    client = request.client.host if request.client else "unknown"
    now = time.time()
    rate_store[client] = [t for t in rate_store[client] if now - t < 60]
    if len(rate_store[client]) >= 100:
        raise HTTPException(status_code=429, detail="Rate limit exceeded (100/min)")
    rate_store[client].append(now)

# Pydantic Models
class ScoreRequest(BaseModel):
    candidate_pillars: Dict[str, float]
    role_weights: Dict[str, float]
    manager_tier: float = 0.7
    resort_complexity: float = 0.5
    location_readiness: float = 0.8

class ShadowRequest(BaseModel):
    current_beliefs: Dict[str, Dict]
    event_pillar: str
    event_outcome: Literal["positive", "negative", "neutral"]
    event_weight: float = 1.0

class DeployRequest(BaseModel):
    candidate_beliefs: Dict[str, Dict]
    role_requirements: Dict[str, float]
    uncertainty_tolerance: float = 0.85

class ExmailRequest(BaseModel):
    segment: str
    season: str
    inventory_level: float
    offer_pool: Optional[List[str]] = None

# Routes
@app.post("/predict-success", dependencies=[Depends(rate_limit)])
def predict(req: ScoreRequest):
    return predict_success(**req.model_dump())

@app.post("/shadow-update", dependencies=[Depends(rate_limit)])
def shadow_update(req: ShadowRequest):
    beliefs = {k: CompetencyBelief(**v, pillar=k) for k, v in req.current_beliefs.items()}
    return process_shadow_event(beliefs, req.event_pillar, req.event_outcome, req.event_weight)

@app.post("/evaluate-deployment", dependencies=[Depends(rate_limit)])
def deploy(req: DeployRequest):
    return evaluate_deployment(**req.model_dump())

@app.post("/optimize-exmail-offer", dependencies=[Depends(rate_limit)])
def exmail_optimize(req: ExmailRequest):
    return optimize_exmail_offer(**req.model_dump())

@app.get("/health")
def health():
    return {"status": "oracle_active", "version": "1.0.0-staging"}
