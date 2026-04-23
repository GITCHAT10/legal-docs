import enum

class TicketStatus(str, enum.Enum):
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_PARTS = "WAITING_PARTS"
    READY_FOR_QC = "READY_FOR_QC"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

class TicketPriority(str, enum.Enum):
    P1 = "P1 Safety"
    P2 = "P2 Revenue Blocking"
    P3 = "P3 Guest Comfort"
    P4 = "P4 Cosmetic"

class TicketSeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
