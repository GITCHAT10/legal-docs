from typing import Callable, Dict, List, Any
import asyncio
import os
import uuid
import logging
from mnos.core.security.guard import guard

class EventDispatcher:
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, listener: Callable):
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)

    def dispatch(self, event_type: str, data: Any, ctx: Dict[str, Any] = None):
        """Dispatches event through ExecutionGuard."""
        if not ctx:
            ctx = {"trace_id": f"EV-{uuid.uuid4().hex[:8]}", "aegis_id": "SYSTEM"}

        def _execute():
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
            return True

        return guard.execute_sovereign_action(f"event.dispatch.{event_type}", ctx, _execute)

event_dispatcher = EventDispatcher()

# --- Cross-module Event Handlers ---

def get_db_session():
    from mnos.core.db.session import SessionLocal
    return SessionLocal()

def handle_reservation_confirmed(data):
    """Subscribed to reservation_confirmed."""
    try:
        from mnos.modules.aqua.transfers.service import create_transfer_request
        from mnos.modules.aqua.transfers.schemas import TransferRequestCreate
        from mnos.modules.aqua.transfers.models import TransferType

        reservation_id = data.get("reservation_id") or data.get("id")
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

# Registering handlers
event_dispatcher.subscribe("reservation_confirmed", handle_reservation_confirmed)
