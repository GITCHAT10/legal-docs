from skyfarm.integration.outbox_service import queue_event
from sqlalchemy.orm import Session
from typing import Dict, Any

def emit_sxos_event(db: Session, tenant_id: str, event_type: str, data: Dict[str, Any]):
    """Standard SXOS emitter that flows to MNOS and SHADOW"""
    # 1. Emit to Event Bus (via Outbox)
    queue_event(db, tenant_id, f"sxos.{event_type.lower()}", data)

    # 2. Local verification log
    print(f"[SXOS EVENT] {event_type} emitted for {tenant_id}")
