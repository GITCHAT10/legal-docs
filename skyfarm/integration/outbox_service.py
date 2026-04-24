from sqlalchemy.orm import Session
from .models import IntegrationOutboxModel
from .service import create_integration_event
import uuid
from typing import Dict, Any

def queue_event(db: Session, tenant_id: str, event_type: str, data: Dict[str, Any]):
    event_id = f"evt_{uuid.uuid4().hex}"
    idempotency_key = f"idem_{uuid.uuid4().hex}"

    event = create_integration_event(
        tenant_id=tenant_id,
        event_type=event_type,
        data=data,
        event_id=event_id
    )

    outbox_entry = IntegrationOutboxModel(
        event_id=event_id,
        event_type=event_type,
        payload_json=event.model_dump(),
        status="pending",
        idempotency_key=idempotency_key
    )

    db.add(outbox_entry)
    db.commit()
    return outbox_entry
