from fastapi import FastAPI, HTTPException, Request
from admiralda_pbx.apps.api.schemas import CallIngest, PBXResponse, RiskMatrix
from admiralda_pbx.services.emotion import emotion_engine
from admiralda_pbx.services.intelligence import intelligence_engine
from admiralda_pbx.services.execution import execution_engine
from admiralda_pbx.services.evidence import evidence_engine
from admiralda_pbx.integrations.mnos.client import mnos_connect
from admiralda_pbx.integrations.telecom.twilio import TwilioAdapter
from admiralda_pbx.apps.api.operator_router import router as operator_router

app = FastAPI(title="ADMIRALDA PBX API (Production)")
telecom = TwilioAdapter()

app.include_router(operator_router, prefix="/api/v1")

@app.post("/api/v1/ingest", response_model=PBXResponse)
async def ingest_call(request: CallIngest):
    """
    Production Ingest Logic: Thresholds + Fail-Closed MNOS.
    """
    # 1. Perception (AI Layer)
    analysis = emotion_engine.analyze(request.transcript)

    # 2. Intelligence (Guardrails)
    context = {"voiceprint_match": request.voiceprint_match}
    decision = intelligence_engine.predict_action(context, analysis)

    # 3. Execution (Whisper / Internal PBX state)
    execution = execution_engine.handle_action(decision, request.call_id, analysis)

    # 4. Fail-Closed MNOS Authority
    if decision == "INITIATE_DUAL_CONFIRMATION":
        mnos_status = await mnos_connect.seal_envelope({"trace_id": f"ASI-{request.call_id}"})
        if mnos_status.get("status") == "FAILED":
            execution["execution_status"] = "FAILED_CLOSED"
            execution["whisper"] = "❌ MNOS unreachable. Execution blocked."
            decision = "FAIL_CLOSED"

    # 5. Risk Scoring
    risk_matrix = RiskMatrix(
        intent_risk="LOW" if analysis["intent_score"] > 0.9 else "HIGH",
        identity_risk="LOW" if request.voiceprint_match > 0.95 else "HIGH",
        financial_risk="MEDIUM",
        overall_score=(analysis["intent_score"] + request.voiceprint_match) / 2
    )

    # 6. Evidence Generation
    envelope = evidence_engine.generate_envelope(
        request.call_id, request.caller_id, request.transcript, analysis, request.tenant_id
    )
    envelope["execution_status"] = execution.get("execution_status", "UNKNOWN")

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

@app.post("/api/v1/webhooks/telecom")
async def telecom_webhook(request: Request):
    """
    Endpoint for real telephony providers (Twilio).
    """
    raw_data = await request.form()
    mapped_data = await telecom.ingest_webhook(dict(raw_data))

    # Process mapped data internally
    return {"status": "accepted", "call_sid": mapped_data["call_id"]}

@app.get("/api/v1/status/{call_id}")
async def get_status(call_id: str, tenant_id: str):
    return {"call_id": call_id, "tenant_id": tenant_id, "status": "ACTIVE"}
