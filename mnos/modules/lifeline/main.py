from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import uuid
from mnos.shared.sdk.client import MnosClient

app = FastAPI(title="MNOS LIFELINE")
mnos_client = MnosClient()

class Patient(BaseModel):
    name: str
    national_id: str
    dob: str

class Encounter(BaseModel):
    patient_id: str
    practitioner_id: str
    type: str

@app.post("/api/lifeline/patients")
async def create_patient(patient: Patient, request: Request):
    transaction_id = str(uuid.uuid4())

    # 1. AEGIS verify
    if not await mnos_client.verify_aegis(request.headers.get("Authorization"), "CREATE", "PATIENT"):
         raise HTTPException(status_code=403, detail="AEGIS verification failed")

    # 2. ELEONE decide
    decision, policy_decision_id = await mnos_client.decide_eleone({"action": "CREATE_PATIENT", "data": patient.model_dump()})
    if decision != "ALLOW":
        raise HTTPException(status_code=403, detail="ELEONE policy denial")

    # 3. Module DB write (mocked)
    patient_id = f"PAT-{uuid.uuid4()}"

    # 4. EVENTS publish
    event_id = await mnos_client.publish_event("PATIENT_CREATED", {"patient_id": patient_id})

    # 5. SHADOW commit
    shadow_id = await mnos_client.commit_shadow(transaction_id, event_id, patient.model_dump())

    return mnos_client.create_response_envelope(
        module="lifeline",
        transaction_id=transaction_id,
        status="success",
        data={"patient_id": patient_id},
        shadow_id=shadow_id,
        event_id=event_id,
        policy_decision_id=policy_decision_id
    )

@app.post("/api/lifeline/encounters")
async def create_encounter(encounter: Encounter, request: Request):
    transaction_id = str(uuid.uuid4())
    # Follows same MNOS transaction order
    return {"status": "success", "transaction_id": transaction_id}

@app.get("/health")
async def health():
    return {"status": "ok"}
