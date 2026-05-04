"""
CHEFS_FARM_OPERATING_MODEL_V1
"""
from sqlalchemy import Column, String, Float, DateTime, JSON, Boolean, ForeignKey
from skyfarm.database import Base
from datetime import datetime
import uuid

class ChefsFarmSiteModel(Base):
    __tablename__ = "chefs_farm_sites"
    chefs_farm_id = Column(String, primary_key=True, default=lambda: f"cf_{uuid.uuid4().hex[:8]}")
    resort_id = Column(String, index=True)
    skyfarm_operator_entity = Column(String, default="SKYFARM_MALDIVES")
    live_link_status = Column(String, default="ONLINE") # ONLINE, OFFLINE
    created_at = Column(DateTime, default=datetime.utcnow)

class FarmOperatorAssignmentModel(Base):
    __tablename__ = "cf_operator_assignments"
    id = Column(String, primary_key=True, default=lambda: f"asgn_{uuid.uuid4().hex[:8]}")
    chefs_farm_id = Column(String, ForeignKey("chefs_farm_sites.chefs_farm_id"))
    farm_operator_id = Column(String)
    status = Column(String, default="ACTIVE")
    assigned_at = Column(DateTime, default=datetime.utcnow)

class ChefHarvestRequestModel(Base):
    __tablename__ = "cf_harvest_requests"
    id = Column(String, primary_key=True, default=lambda: f"req_{uuid.uuid4().hex[:8]}")
    chefs_farm_id = Column(String, ForeignKey("chefs_farm_sites.chefs_farm_id"))
    chef_id = Column(String)
    crop_batch_id = Column(String)
    container_id = Column(String)
    harvest_request_status = Column(String, default="PENDING") # PENDING, APPROVED, COMPLETED, CANCELLED
    requested_at = Column(DateTime, default=datetime.utcnow)

class ChefAcceptanceRecordModel(Base):
    __tablename__ = "cf_acceptance_records"
    id = Column(String, primary_key=True, default=lambda: f"acc_{uuid.uuid4().hex[:8]}")
    chefs_farm_id = Column(String, ForeignKey("chefs_farm_sites.chefs_farm_id"))
    chef_id = Column(String)
    harvest_request_id = Column(String)
    accepted_kg = Column(Float)
    rejected_kg = Column(Float)
    chef_confirmation_id = Column(String, unique=True)
    fce_settlement_status = Column(String, default="PENDING") # PENDING, PAID, REJECTED
    shadow_proof_hash = Column(String)
    guest_story_qr_status = Column(String, default="GENERATED")
    confirmed_at = Column(DateTime, default=datetime.utcnow)

class ChefFeedbackRecordModel(Base):
    __tablename__ = "cf_feedback_records"
    id = Column(String, primary_key=True, default=lambda: f"fdb_{uuid.uuid4().hex[:8]}")
    chefs_farm_id = Column(String, ForeignKey("chefs_farm_sites.chefs_farm_id"))
    chef_id = Column(String)
    crop_batch_id = Column(String)
    feedback_text = Column(String)
    metadata_json = Column(JSON) # e.g., preferred_harvest_time, crop_preference
    created_at = Column(DateTime, default=datetime.utcnow)
