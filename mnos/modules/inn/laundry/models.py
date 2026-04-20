from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, Float
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from mnos.core.db.base_class import Base

class LaundryStatus(str, enum.Enum):
    PENDING = "pending"
    COLLECTED = "collected"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class LaundryItem(Base):
    id = Column(Integer, primary_key=True, index=True)
    folio_id = Column(Integer, ForeignKey("folio.id"), nullable=False)
    guest_id = Column(Integer, ForeignKey("guest.id"), nullable=False)
    status = Column(Enum(LaundryStatus), default=LaundryStatus.PENDING)
    description = Column(String)
    item_count = Column(Integer, default=1)
    total_price = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    folio = relationship("Folio")
    guest = relationship("Guest")
