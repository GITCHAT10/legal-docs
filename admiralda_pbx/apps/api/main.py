from fastapi import FastAPI, HTTPException
from admiralda_pbx.apps.api.schemas import CallIngest, PBXResponse, RiskMatrix
from admiralda_pbx.services.emotion import emotion_engine
from admiralda_pbx.services.intelligence import intelligence_engine
from admiralda_pbx.services.execution import execution_engine
from admiralda_pbx.services.evidence import evidence_engine
from admiralda_pbx.integrations.mnos.client import mnos_connect

app = FastAPI(title="ADMIRALDA PBX API (Hardened)")

@app.post("/api/v1/ingest", response_model=PBXResponse)
async def ingest_call(request: CallIngest):
    """
    Hardened Ingest Logic: Process call events with thresholds and fail-closed MNOS integration.
    """
    # 1. Perception
    analysis = emotion_engine.analyze(request.transcript)

    # 2. Interpretation with Guardrails
    context = {"voiceprint_match": request.voiceprint_match}
    decision = intelligence_engine.predict_action(context, analysis)

    # 3. Execution handling (Whisper + Status)
    execution = execution_engine.handle_action(decision, request.call_id, analysis)

    # 4. Fail-Closed MNOS Logic
    # Simulation: If we need a sovereign seal, check MNOS connectivity
    if decision == "INITIATE_DUAL_CONFIRMATION":
        mnos_status = await mnos_connect.seal_envelope({"trace_id": "test"})
        if mnos_status.get("status") == "FAILED":
            execution["execution_status"] = "FAILED_CLOSED"
            execution["whisper"] = "❌ MNOS Sovereign Layer unreachable. Execution blocked for safety."
            decision = "FAIL_CLOSED"

    # 5. Risk Matrix Generation
    risk_matrix = RiskMatrix(
        intent_risk="LOW" if analysis["intent_score"] > 0.9 else "HIGH",
        identity_risk="LOW" if request.voiceprint_match > 0.95 else "HIGH",
        financial_risk="MEDIUM",
        overall_score=(analysis["intent_score"] + request.voiceprint_match) / 2
    )

    # 6. Evidence Envelope Generation
    envelope = evidence_engine.generate_envelope(
        request.call_id,
        request.caller_id,
        request.transcript,
        analysis,
        request.tenant_id
    )

    # Update envelope with extended metadata
    envelope["consent_confirmed"] = False # Default until dual-confirmation
    envelope["execution_status"] = execution.get("execution_status", "UNKNOWN")
    envelope["verification_method"] = "VOICE_BIOMETRIC"
    envelope["jurisdiction"] = "Maldives"

    return PBXResponse(
        status="PROCESSED",
        trace_id=f"ASI-{request.call_id}",
        call_id=request.call_id,
        tenant_id=request.tenant_id,
        decision=decision,
        execution_status=execution.get("execution_status", "UNKNOWN"),
        evidence_envelope=envelope,
        whisper_assist=execution.get("whisper"),
        risk_matrix=risk_matrix
    )

@app.get("/api/v1/status/{call_id}")
async def get_status(call_id: str, tenant_id: str):
    return {"call_id": call_id, "tenant_id": tenant_id, "status": "ACTIVE"}
