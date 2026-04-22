from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class PatientBase(BaseModel):
    national_id: str
    efaas_id: Optional[str] = None
    full_name: str
    dob: datetime
    gender: str
    contact_info: Optional[Dict[str, Any]] = None
    is_maternal_risk: bool = False
    gestational_age: Optional[int] = None
    fhir_resource: Optional[Dict[str, Any]] = None
    mihis_id: Optional[str] = None
    biometric_token: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class Patient(PatientBase):
    id: str
    model_config = ConfigDict(from_attributes=True)

class EncounterBase(BaseModel):
    patient_id: str
    type: str
    atoll_hub_id: str
    vitals: Optional[Dict[str, Any]] = None
    clinical_notes: Optional[str] = None
    icd10_codes: List[str] = []
    fhir_encounter: Optional[Dict[str, Any]] = None

class EncounterCreate(EncounterBase):
    practitioner_id: int

class Encounter(EncounterBase):
    id: str
    practitioner_id: int
    status: str
    is_ai_suggestion: bool
    human_signature_id: Optional[str] = None
    risk_level: str
    transport_token: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ClaimBase(BaseModel):
    encounter_id: str
    payer_id: str
    base_amount: float
    currency: str = "MVR"
    vira_token: Optional[str] = None

class ClaimCreate(ClaimBase):
    pass

class Claim(ClaimBase):
    id: str
    service_charge: float
    subtotal: float
    tax_amount: float
    total_amount: float
    tax_point_date: datetime
    exchange_rate: float
    aasandha_coverage: float
    patient_copay: float
    status: str
    ledger_anchor_id: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
