from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class AegisIdentityProfile(Base):
    __tablename__ = 'aegis_identity_profiles'
    identity_id = Column(UUID(as_uuid=True), primary_key=True)
    profile_type = Column(String(30), nullable=False) # staff, supplier, etc
    external_ref = Column(String(100))
    full_name = Column(String(150))
    organization_id = Column(UUID(as_uuid=True))
    department_id = Column(UUID(as_uuid=True))
    role_code = Column(String(50))
    national_id_hash = Column(String(255))
    mobile_hash = Column(String(255))
    email_hash = Column(String(255))
    verification_status = Column(String(30), default='pending')
    identity_status = Column(String(30), default='active')
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class AegisIdentityDevice(Base):
    __tablename__ = 'aegis_identity_devices'
    device_id = Column(UUID(as_uuid=True), primary_key=True)
    identity_id = Column(UUID(as_uuid=True), ForeignKey('aegis_identity_profiles.identity_id'))
    device_fingerprint_hash = Column(String(255), nullable=False)
    device_label = Column(String(100))
    trust_level = Column(String(20), default='low')
    is_primary = Column(Boolean, default=False)
    last_seen_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

class AegisIdentityRole(Base):
    __tablename__ = 'aegis_identity_roles'
    binding_id = Column(UUID(as_uuid=True), primary_key=True)
    identity_id = Column(UUID(as_uuid=True), ForeignKey('aegis_identity_profiles.identity_id'))
    role_name = Column(String(100), nullable=False)
    scope_type = Column(String(30))
    scope_ref = Column(UUID(as_uuid=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

class AegisIdentityConsent(Base):
    __tablename__ = 'aegis_identity_consents'
    consent_id = Column(UUID(as_uuid=True), primary_key=True)
    identity_id = Column(UUID(as_uuid=True), ForeignKey('aegis_identity_profiles.identity_id'))
    consent_type = Column(String(50), nullable=False)
    consent_version = Column(String(30))
    granted = Column(Boolean, default=False)
    granted_at = Column(DateTime)
    revoked_at = Column(DateTime)

class AegisIdentityVerification(Base):
    __tablename__ = 'aegis_identity_verifications'
    verification_id = Column(UUID(as_uuid=True), primary_key=True)
    identity_id = Column(UUID(as_uuid=True), ForeignKey('aegis_identity_profiles.identity_id'))
    verification_method = Column(String(50))
    verification_result = Column(String(30))
    verifier_identity_id = Column(UUID(as_uuid=True))
    notes = Column(Text)
    verified_at = Column(DateTime, server_default=func.now())

class AegisIdentityAction(Base):
    __tablename__ = 'aegis_identity_actions'
    action_id = Column(UUID(as_uuid=True), primary_key=True)
    identity_id = Column(UUID(as_uuid=True), ForeignKey('aegis_identity_profiles.identity_id'))
    device_id = Column(UUID(as_uuid=True), ForeignKey('aegis_identity_devices.device_id'))
    action_type = Column(String(50), nullable=False)
    module_name = Column(String(50))
    target_ref = Column(String(100))
    location_tag = Column(String(100))
    action_status = Column(String(30), default='accepted')
    created_at = Column(DateTime, server_default=func.now())

class AegisAssetBinding(Base):
    __tablename__ = 'aegis_asset_bindings'
    binding_id = Column(UUID(as_uuid=True), primary_key=True)
    identity_id = Column(UUID(as_uuid=True), ForeignKey('aegis_identity_profiles.identity_id'))
    asset_type = Column(String(50), nullable=False)
    asset_ref = Column(String(100), nullable=False)
    binding_status = Column(String(30), default='active')
    bound_at = Column(DateTime, server_default=func.now())
    released_at = Column(DateTime)

class AegisDeliveryAcceptance(Base):
    __tablename__ = 'aegis_delivery_acceptance'
    acceptance_id = Column(UUID(as_uuid=True), primary_key=True)
    batch_id = Column(UUID(as_uuid=True))
    identity_id = Column(UUID(as_uuid=True), ForeignKey('aegis_identity_profiles.identity_id'))
    device_id = Column(UUID(as_uuid=True), ForeignKey('aegis_identity_devices.device_id'))
    delivery_condition = Column(String(30))
    notes = Column(Text)
    accepted_at = Column(DateTime, server_default=func.now())
