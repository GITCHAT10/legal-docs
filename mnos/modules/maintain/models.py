from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from mnos.core.db.base_class import Base
from .enums import TicketStatus, TicketPriority, TicketSeverity

class MaintenanceTicket(Base):
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("room.id"), nullable=False)
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN)
    priority = Column(Enum(TicketPriority), default=TicketPriority.P3)
    severity = Column(Enum(TicketSeverity), default=TicketSeverity.MEDIUM)
    title = Column(String, nullable=False)
    description = Column(String)
    assigned_to = Column(String)
    is_blocking = Column(Boolean, default=False)
    sla_deadline = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime)
    closed_at = Column(DateTime)

    room = relationship("Room")
