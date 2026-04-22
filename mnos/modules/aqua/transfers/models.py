from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from mnos.core.db.base_class import Base

class TransferType(str, enum.Enum):
    BOAT = "boat"
    SEAPLANE = "seaplane"
    TAXI = "taxi"

class TransferStatus(str, enum.Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Vehicle(Base):
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False, default="default")
    trace_id = Column(String, index=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, default="SYSTEM")

    name = Column(String, nullable=False)
    type = Column(Enum(TransferType), nullable=False)
    capacity = Column(Integer)
    license_plate = Column(String)

    __table_args__ = (UniqueConstraint('tenant_id', 'trace_id', name='_vehicle_tenant_trace_uc'),)

class TransferRequest(Base):
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False, default="default")
    trace_id = Column(String, index=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, default="SYSTEM")

    external_reservation_id = Column(String, index=True, nullable=False)
    type = Column(Enum(TransferType), nullable=False)
    status = Column(Enum(TransferStatus), default=TransferStatus.PENDING)
    pickup_time = Column(DateTime)
    eta = Column(DateTime)
    pickup_location = Column(String)
    destination = Column(String)
    vehicle_id = Column(Integer, ForeignKey("vehicle.id"))

    vehicle = relationship("Vehicle")
    __table_args__ = (UniqueConstraint('tenant_id', 'trace_id', name='_transfer_tenant_trace_uc'),)

class Manifest(Base):
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False, default="default")
    trace_id = Column(String, index=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, default="SYSTEM")

    transfer_request_id = Column(Integer, ForeignKey("transferrequest.id"), nullable=False)
    guest_id = Column(Integer, ForeignKey("guest.id"), nullable=False)

    transfer_request = relationship("TransferRequest")
    guest = relationship("Guest")

    __table_args__ = (UniqueConstraint('tenant_id', 'trace_id', name='_manifest_tenant_trace_uc'),)
