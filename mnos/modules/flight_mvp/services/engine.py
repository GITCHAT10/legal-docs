from sqlalchemy.orm import Session
from mnos.modules.flight_mvp.models import models
from datetime import datetime, UTC, timedelta
from typing import Optional, Dict, Any
import uuid

class FlightMVPEngine:
    """
    MVP Flight Tracking Engine.
    Rule: delay > 30min -> auto-adjust UT + notify guest.
    """

    async def create_mvp_session(
        self,
        db: Session,
        *,
        booking_id: str,
        flight_number: str,
        origin_iata: str,
        scheduled_arrival: datetime,
        guest_count: int,
        ut_ticket_ref: Optional[str] = None
    ) -> models.FlightMvpSession:

        # 1. Fetch flight data (Mock FlightAware)
        flight_data = {
            "status": models.FlightStatus.SCHEDULED,
            "scheduled_departure": scheduled_arrival - timedelta(hours=4),
            "estimated_arrival": scheduled_arrival,
            "delay_minutes": 0
        }

        # 2. Create Session
        session = models.FlightMvpSession(
            session_ref=f"PH-FLT-MVP-{uuid.uuid4().hex[:6].upper()}",
            booking_id=booking_id,
            flight_number=flight_number,
            origin_iata=origin_iata,
            scheduled_departure_utc=flight_data["scheduled_departure"],
            scheduled_arrival_utc=scheduled_arrival,
            estimated_arrival_utc=flight_data["estimated_arrival"],
            flight_status=flight_data["status"],
            delay_minutes=flight_data["delay_minutes"],
            guest_count=guest_count,
            ut_ticket_ref=ut_ticket_ref
        )
        session.ensure_trace_id()
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    async def check_for_delays(self, db: Session, session_id: int):
        session = db.query(models.FlightMvpSession).filter(models.FlightMvpSession.id == session_id).first()
        if not session: return

        # Mock updated data with delay
        delay = 45
        if delay > 30:
            session.delay_minutes = delay
            session.flight_status = models.FlightStatus.DELAYED

            # Auto-adjust UT
            if session.ut_auto_adjust_enabled and session.ut_ticket_ref:
                # Log event
                event = models.FlightMvpEvent(
                    flight_session_id=session.id,
                    event_time=datetime.now(UTC),
                    event_type="ut_adjusted",
                    event_data=f"Delay {delay}min detected. Buffer added."
                )
                event.ensure_trace_id()
                db.add(event)

                # Mock UT adjustment
                print(f"UT_AUTO_ADJUST: Flight {session.flight_number} delayed {delay}min. Adjusting ticket {session.ut_ticket_ref}")

            db.commit()

flight_mvp_engine = FlightMVPEngine()
