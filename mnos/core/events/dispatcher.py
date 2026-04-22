from typing import Callable, Dict, List, Any
import asyncio
import os
import uuid
import logging

class EventDispatcher:
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, listener: Callable):
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)

    def dispatch(self, event_type: str, data: Any):
        if event_type in self._listeners:
            for listener in self._listeners[event_type]:
                if asyncio.iscoroutinefunction(listener):
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            loop.create_task(listener(data))
                        else:
                            loop.run_until_complete(listener(data))
                    except Exception as e:
                        logging.error(f"Async listener error: {e}")
                else:
                    try:
                        listener(data)
                    except Exception as e:
                        logging.error(f"Sync listener error: {e}")

event_dispatcher = EventDispatcher()

# --- Cross-module Event Handlers ---

def get_db_session():
    # Helper to get session without circular imports or broken test paths
    from mnos.core.db.session import SessionLocal
    return SessionLocal()

def handle_reservation_confirmed(data):
    # Fix reservation event mismatch: ensure data keys match expectation
    reservation_id = data.get("reservation_id") or data.get("id")
    if not reservation_id:
        logging.warning("Reservation confirmed event missing ID")
        return

    try:
        from mnos.modules.aqua.transfers.service import create_transfer_request
        from mnos.modules.aqua.transfers.schemas import TransferRequestCreate
        from mnos.modules.aqua.transfers.models import TransferType

        db = get_db_session()
        try:
            transfer_in = TransferRequestCreate(
                external_reservation_id=str(reservation_id),
                type=TransferType.BOAT,
                pickup_location="Velana International Airport",
                destination="Resort Island",
                trace_id=f"AUTO-TRANS-{uuid.uuid4().hex[:8]}"
            )
            create_transfer_request(db, request_in=transfer_in)
        finally:
            db.close()
    except ImportError:
        pass

def handle_housekeeping_completed(data):
    room_id = data.get("room_id") or data.get("id")
    if not room_id:
        return

    try:
        from mnos.modules.inn.reservations.service import mark_room_ready_from_housekeeping

        db = get_db_session()
        try:
            mark_room_ready_from_housekeeping(db, room_id)
        finally:
            db.close()
    except ImportError:
        pass

# Registering handlers
event_dispatcher.subscribe("reservation_confirmed", handle_reservation_confirmed)
event_dispatcher.subscribe("housekeeping_completed", handle_housekeeping_completed)
