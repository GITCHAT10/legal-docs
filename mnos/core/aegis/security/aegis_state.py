import enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from mnos.core.db.base_class import Base
from datetime import datetime

class SystemState(str, enum.Enum):
    OPTIMAL = "OPTIMAL"
    DEGRADED = "DEGRADED"
    PROTECTED = "PROTECTED"
    EMERGENCY = "EMERGENCY"

class GlobalState(Base):
    """
    AEGIS Sovereign State Lock.
    Governs global execution policies.
    """
    id = Column(Integer, primary_key=True, index=True)
    state = Column(Enum(SystemState), default=SystemState.OPTIMAL)
    reason = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String)

def set_system_state(db, state: SystemState, actor: str, reason: str = None):
    current = db.query(GlobalState).first()
    if not current:
        current = GlobalState()
        db.add(current)

    current.state = state
    current.updated_by = actor
    current.reason = reason
    db.commit()
    return current

def get_system_state(db) -> SystemState:
    current = db.query(GlobalState).first()
    return current.state if current else SystemState.OPTIMAL

def is_protection_mode(db) -> bool:
    return get_system_state(db) == SystemState.PROTECTED
