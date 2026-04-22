from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON, Boolean
from sqlalchemy.orm import relationship
from mnos.core.db.base_class import Base
import datetime

class Patient(Base):
    __tablename__ = "nexama_patients"
    id = Column(String, primary_key=True, index=True)
    national_id = Column(String, unique=True, index=True)
    efaas_id = Column(String, unique=True, index=True) # Maldives National Digital Identity
    full_name = Column(String)
    dob = Column(DateTime)
    gender = Column(String)
    contact_info = Column(JSON)
    # FHIR Interop
    fhir_resource = Column(JSON)
    mihis_id = Column(String, index=True) # MIHIS / DHIS2 link
    # Biometric/Identity
    biometric_token = Column(String, nullable=True)
    # Maternal and Child Health
    is_maternal_risk = Column(Boolean, default=False)
    gestational_age = Column(Integer, nullable=True) # in weeks
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Encounter(Base):
    __tablename__ = "nexama_encounters"
    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, ForeignKey("nexama_patients.id"))
    practitioner_id = Column(Integer, ForeignKey("users.id"))
    atoll_hub_id = Column(String, index=True) # Island/Atoll identifier
    type = Column(String) # OP, IP, Emergency
    status = Column(String)
    clinical_notes = Column(String)
    icd10_codes = Column(JSON)
    fhir_encounter = Column(JSON)
    vitals = Column(JSON)
    diagnostics = Column(JSON)
    prescriptions = Column(JSON)
    # Safety Guardrails
    is_ai_suggestion = Column(Boolean, default=True)
    human_signature_id = Column(String, nullable=True)
    risk_level = Column(String, default="NORMAL")
    # Logistics
    transport_token = Column(String, nullable=True) # AQUA/ATOLLAIRWAYS link
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Claim(Base):
    __tablename__ = "nexama_claims"
    id = Column(String, primary_key=True, index=True)
    encounter_id = Column(String, ForeignKey("nexama_encounters.id"))
    payer_id = Column(String) # 'Aasandha', 'Self', etc.
    vira_token = Column(String, nullable=True) # Aasandha Vira Portal link

    # MIRA Audit-Proof Structure
    base_amount = Column(Float)
    service_charge = Column(Float) # 10%
    subtotal = Column(Float) # Base + SC
    tax_amount = Column(Float) # 17% TGST on Subtotal
    total_amount = Column(Float) # Subtotal + Tax

    currency = Column(String, default="MVR")
    exchange_rate = Column(Float, default=1.0)
    tax_point_date = Column(DateTime, default=datetime.datetime.utcnow)

    # Aasandha Split Logic
    aasandha_coverage = Column(Float, default=0.0)
    patient_copay = Column(Float, default=0.0)

    status = Column(String)
    ledger_anchor_id = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
