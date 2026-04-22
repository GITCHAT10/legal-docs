from fastapi import APIRouter, HTTPException, Request, Depends, Query
from typing import List, Dict, Any
import uuid
from mnos.modules.nexama.schemas.health import PatientCreate, Patient, EncounterCreate, Encounter, ClaimCreate, Claim
from mnos.modules.nexama.services.clinical import clinical_service
from mnos.modules.nexama.services.finance import finance_service
from mnos.modules.nexama.services.identity import identity_service
from mnos.shared.sdk.client import mnos_client

router = APIRouter(prefix="/api/nexama", tags=["NEXAMA HEALTH CARE ENGINE"])

@router.post("/patients", response_model=Patient, summary="Register a new patient", description="Enforces eFaas (MDS) identity verification and MNOS sovereign law.")
async def create_patient(patient: PatientCreate, request: Request):
    transaction_id = str(uuid.uuid4())

    # 1. AEGIS Security Gate
    if not await mnos_client.verify_aegis(request.headers.get("Authorization"), "CREATE", "PATIENT"):
        raise HTTPException(status_code=403, detail="AEGIS identity failure")

    # 2. eFaas Handshake (MANDATORY for Maldives 2.0)
    efaas_data = await identity_service.verify_efaas(request.headers.get("X-EFAAS-TOKEN"))
    if efaas_data["status"] != "SUCCESS":
        raise HTTPException(status_code=401, detail=f"eFaas Verification Failed: {efaas_data['reason']}")

    # 3. ELEONE Governance Policy
    decision, policy_id = await mnos_client.decide_eleone({"action": "REGISTER_PATIENT", "jurisdiction": "MV"})
    if decision != "ALLOW":
        raise HTTPException(status_code=403, detail="ELEONE policy block")

    # 4. DB Persistence (Mocked)
    patient_id = f"PAT-{uuid.uuid4().hex[:8]}"

    # Enrich with eFaas ID
    patient_payload = {**patient.model_dump(), "id": patient_id, "efaas_id": efaas_data["efaas_id"]}

    # 5. EVENTS Dispatch
    event_id = await mnos_client.publish_event("nexama.patient.registered", {"patient_id": patient_id, "efaas_id": efaas_data["efaas_id"]})

    # 6. SHADOW Audit
    shadow_id = await mnos_client.commit_shadow(transaction_id, event_id, patient_payload)

    return patient_payload

@router.post("/encounters", response_model=Encounter, summary="Initialize clinical encounter", description="SILVIA AI diagnostics + Island Logistics + Emergency Overrides.")
async def create_encounter(encounter: EncounterCreate, request: Request):
    transaction_id = str(uuid.uuid4())

    # 1. AEGIS
    if not await mnos_client.verify_aegis(request.headers.get("Authorization"), "CREATE", "ENCOUNTER"):
        raise HTTPException(status_code=403, detail="AEGIS identity failure")

    # 2. Clinical ASI Execution (includes SILVIA + Island Logistics)
    result = await clinical_service.create_encounter(encounter.model_dump())

    # 3. EVENTS
    event_id = await mnos_client.publish_event("nexama.encounter.created", result)

    # 4. SHADOW
    shadow_id = await mnos_client.commit_shadow(transaction_id, event_id, result)

    return {
        **encounter.model_dump(),
        "id": result["id"],
        "status": result["status"],
        "is_ai_suggestion": result["is_ai_suggestion"],
        "risk_level": result["risk_level"],
        "created_at": "2024-04-22T12:00:00Z"
    }

@router.post("/claims", response_model=Claim, summary="Generate MIRA/Aasandha claim", description="Real-time Vira portal clearing and audit-proof TGST logic.")
async def create_claim(claim: ClaimCreate, request: Request):
    transaction_id = str(uuid.uuid4())

    # 1. AEGIS
    if not await mnos_client.verify_aegis(request.headers.get("Authorization"), "CREATE", "CLAIM"):
        raise HTTPException(status_code=403, detail="AEGIS identity failure")

    # 2. Finance Engine Execution (MIRA TGST 17% + Aasandha Vira clearing)
    result = await finance_service.generate_claim(claim.encounter_id, claim.payer_id, claim.base_amount)

    # 3. EVENTS
    event_id = await mnos_client.publish_event("nexama.claim.generated", result)

    # 4. SHADOW
    shadow_id = await mnos_client.commit_shadow(transaction_id, event_id, result)

    return {
        **claim.model_dump(),
        "id": result["id"],
        "service_charge": result["service_charge"],
        "subtotal": result["subtotal"],
        "tax_amount": result["tax_amount"],
        "total_amount": result["total_amount"],
        "tax_point_date": result["tax_point_date"],
        "exchange_rate": result["exchange_rate_locked"],
        "aasandha_coverage": result["aasandha_coverage"],
        "patient_copay": result["patient_copay"],
        "status": result["status"],
        "ledger_anchor_id": result["ledger_anchor"]
    }

@router.get("/queue/token", summary="Get Biometric Queue Token", description="Patent AL: eFaas-linked queue orchestration.")
async def get_queue_token(efaas_id: str, facility_id: str, request: Request):
    token = await identity_service.get_biometric_queue_token(efaas_id, facility_id)
    return {"token": token}
