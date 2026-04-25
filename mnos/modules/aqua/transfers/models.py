from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
import enum

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

from mnos.core.db.base_class import Base
class Vehicle(Base):
    __tablename__ = "vehicle"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(Enum(TransferType), nullable=False)
    capacity = Column(Integer)
    license_plate = Column(String)

from mnos.core.db.base_class import Base
class TransferRequest(Base):
    __tablename__ = "transferrequest"
    id = Column(Integer, primary_key=True, index=True)
    reservation_id = Column(Integer, ForeignKey("reservation.id"), nullable=False)
    type = Column(Enum(TransferType), nullable=False)
    status = Column(Enum(TransferStatus), default=TransferStatus.PENDING)
    pickup_time = Column(DateTime)
    eta = Column(DateTime)
    pickup_location = Column(String)
    destination = Column(String)
    vehicle_id = Column(Integer, ForeignKey("vehicle.id"))

    reservation = relationship("Reservation")
    vehicle = relationship("Vehicle")

from mnos.core.db.base_class import Base
class Manifest(Base):
    __tablename__ = "manifest"
    id = Column(Integer, primary_key=True, index=True)
    transfer_request_id = Column(Integer, ForeignKey("transferrequest.id"), nullable=False)
    guest_id = Column(Integer, ForeignKey("guest.id"), nullable=False)

    transfer_request = relationship("TransferRequest")
    guest = relationship("Guest")
