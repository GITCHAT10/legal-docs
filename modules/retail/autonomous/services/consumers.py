from sqlalchemy.orm import Session
from ..models.database import RetailSession, SessionLocal
from .adapters import EVENTSAdapter, SHADOWAdapter
import uuid

async def handle_aegis_user_suspended(payload: dict):
    """
    Consumer for aegis.user_suspended.
    If a user is suspended, we should flag any of their ACTIVE retail sessions.
    """
    aegis_user_id = payload.get("aegis_user_id")
    if not aegis_user_id:
        return

    db = SessionLocal()
    events = EVENTSAdapter()
    shadow = SHADOWAdapter()

    try:
        active_sessions = db.query(RetailSession).filter(
            RetailSession.aegis_user_id == uuid.UUID(aegis_user_id),
            RetailSession.status.in_(["OPEN", "ACTIVE"])
        ).all()

        for session in active_sessions:
            session.status = "FLAGGED"
            db.commit()

            await events.publish("retail.session_flagged", {
                "session_id": str(session.id),
                "reason": "USER_SUSPENDED_BY_AEGIS"
            })

            await shadow.commit({
                "tenant_id": str(session.tenant_id),
                "trace_id": str(session.trace_id),
                "entity_type": "A_RETAIL_SESSION",
                "entity_id": str(session.id),
                "event_type": "FLAGGED",
                "payload": {"reason": "USER_SUSPENDED_BY_AEGIS", "aegis_payload": payload}
            })
    finally:
        db.close()

async def handle_fce_settlement_failed(payload: dict):
    """
    Consumer for fce.settlement_failed.
    """
    session_id = payload.get("session_id")
    if not session_id:
        return

    db = SessionLocal()
    try:
        session = db.query(RetailSession).filter(RetailSession.id == uuid.UUID(session_id)).first()
        if session:
            session.status = "FLAGGED"
            db.commit()
    finally:
        db.close()
