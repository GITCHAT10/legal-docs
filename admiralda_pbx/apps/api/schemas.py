from pydantic import BaseModel, Field
from typing import Dict, Optional, Any, List

class CallIngest(BaseModel):
    tenant_id: str
    caller_id: str
    call_id: str
    transcript: str
    voiceprint_match: Optional[float] = 1.0

class EvidenceEnvelope(BaseModel):
    call_id: str
    tenant_id: str
    caller_id: str
    timestamp: str
    audio_hash: str
    transcript_hash: str
    intent_score: float
    sentiment_score: float
    confidence_score: float
    envelope_hash: str
    # Extended Metadata
    consent_confirmed: bool = False
    jurisdiction: str = "Maldives"
    verification_method: str = "VOICE_BIOMETRIC"
    execution_status: str = "UNKNOWN"

class RiskMatrix(BaseModel):
    intent_risk: str
    identity_risk: str
    financial_risk: str
    overall_score: float

class PBXResponse(BaseModel):
    trace_id: str
    status: str
    call_id: str
    tenant_id: str
    decision: str
    execution_status: str
    evidence_envelope: Optional[EvidenceEnvelope] = None
    whisper_assist: Optional[str] = None
    risk_matrix: RiskMatrix
