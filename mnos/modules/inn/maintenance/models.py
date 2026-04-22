from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

class MaintenanceStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class MaintenancePriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

from mnos.core.db.base_class import Base
class MaintenanceTicket(Base):
    __tablename__ = "maintenanceticket"
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("room.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(String)
    status = Column(Enum(MaintenanceStatus), default=MaintenanceStatus.OPEN)
    priority = Column(Enum(MaintenancePriority), default=MaintenancePriority.MEDIUM)
    assigned_to = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)

    room = relationship("Room")
