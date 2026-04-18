from sqlalchemy.orm import Session
from .models import TraceRecordModel
from skyfarm.integration.outbox_service import queue_event
import uuid
import json

def record_custody_transfer(db: Session, item_id: str, from_actor: str, to_actor: str, tenant_id: str):
    record = TraceRecordModel(
        id=f"trc_{uuid.uuid4().hex[:8]}",
        item_id=item_id,
        action="custody_transfer",
        actor_id=to_actor,
        metadata_json=json.dumps({"from": from_actor, "to": to_actor})
    )
    db.add(record)

    # Queue event
    queue_event(db, tenant_id, "trace.custody_transfer", {
        "item_id": item_id,
        "from": from_actor,
        "to": to_actor
    })

    db.commit()
    db.refresh(record)
    return record

def record_digital_twin_created(db: Session, item_id: str, actor_id: str, tenant_id: str, metadata: dict = {}):
    record = TraceRecordModel(
        id=f"trc_{uuid.uuid4().hex[:8]}",
        item_id=item_id,
        action="digital_twin_created",
        actor_id=actor_id,
        metadata_json=json.dumps(metadata)
    )
    db.add(record)

    # Queue event
    queue_event(db, tenant_id, "trace.digital_twin_created", {
        "item_id": item_id,
        "metadata": metadata
    })

    db.commit()
    db.refresh(record)
    return record
