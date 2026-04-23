from typing import List, Optional
from sqlalchemy.orm import Session
from . import models, enums
from mnos.modules.inn.reservations.models import Room, RoomStatus
from mnos.modules.shadow import service as shadow_service
from datetime import datetime, timedelta
import uuid

def create_ticket(db: Session, room_id: int, title: str, description: str, priority: enums.TicketPriority, severity: enums.TicketSeverity = enums.TicketSeverity.MEDIUM, actor: str = "SYSTEM") -> models.MaintenanceTicket:
    try:
        is_blocking = priority in [enums.TicketPriority.P1, enums.TicketPriority.P2] or severity == enums.TicketSeverity.CRITICAL
        trace_id = f"MAINT-CREATE-{uuid.uuid4().hex[:8]}"

        # Simple SLA calculation
        sla_hours = {"P1 Safety": 2, "P2 Revenue Blocking": 4, "P3 Guest Comfort": 12, "P4 Cosmetic": 48}
        deadline = datetime.utcnow() + timedelta(hours=sla_hours.get(priority.value, 24))

        ticket = models.MaintenanceTicket(
            room_id=room_id,
            trace_id=trace_id,
            title=title,
            description=description,
            priority=priority,
            severity=severity,
            status=enums.TicketStatus.OPEN,
            is_blocking=is_blocking,
            sla_deadline=deadline
        )
        db.add(ticket)

        room_before = None
        room_after = None
        if is_blocking:
            room = db.query(Room).filter(Room.id == room_id).first()
            if room:
                room_before = {"status": room.status}
                room.status = RoomStatus.MAINTENANCE
                room_after = {"status": room.status}

        db.flush()
        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor, "action": "CREATE_MAINTENANCE_TICKET", "entity_type": "MAINTENANCE_TICKET", "entity_id": ticket.id,
            "after_state": {"room_id": room_id, "priority": priority, "is_blocking": is_blocking, "sla_deadline": deadline.isoformat()}
        })

        db.commit()
        db.refresh(ticket)
        return ticket
    except Exception:
        db.rollback()
        raise

def update_ticket_status(db: Session, ticket_id: int, new_status: enums.TicketStatus, actor: str = "SYSTEM") -> models.MaintenanceTicket:
    try:
        ticket = db.query(models.MaintenanceTicket).filter(models.MaintenanceTicket.id == ticket_id).first()
        if not ticket: raise ValueError("Ticket not found")

        trace_id = f"MAINT-STATUS-{uuid.uuid4().hex[:8]}"
        before_state = {"status": ticket.status}

        room_change = None
        if new_status == enums.TicketStatus.RESOLVED:
            ticket.resolved_at = datetime.utcnow()
        elif new_status == enums.TicketStatus.CLOSED:
            ticket.closed_at = datetime.utcnow()
            if ticket.is_blocking:
                other_blocking = db.query(models.MaintenanceTicket).filter(
                    models.MaintenanceTicket.room_id == ticket.room_id,
                    models.MaintenanceTicket.is_blocking == True,
                    models.MaintenanceTicket.status != enums.TicketStatus.CLOSED,
                    models.MaintenanceTicket.id != ticket_id
                ).first()
                if not other_blocking:
                    room = db.query(Room).filter(Room.id == ticket.room_id).first()
                    if room:
                        room_before = room.status
                        room.status = RoomStatus.READY
                        room_change = {"before": room_before, "after": room.status}

        ticket.status = new_status
        db.flush()
        shadow_service.commit_evidence(db, trace_id, {
            "actor": actor, "action": "UPDATE_MAINTENANCE_STATUS", "entity_type": "MAINTENANCE_TICKET", "entity_id": ticket_id,
            "before_state": before_state, "after_state": {"status": new_status, "room_change": room_change}
        })
        db.commit()
        db.refresh(ticket)
        return ticket
    except Exception:
        db.rollback()
        raise
