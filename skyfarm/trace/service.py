from sqlalchemy.orm import Session
from .models import TraceRecordModel
import uuid
import json

def update_trace(db: Session, item_id: str, action: str, actor_id: str, metadata: dict = {}):
    record = TraceRecordModel(
        id=f"trace_{uuid.uuid4().hex[:8]}",
        item_id=item_id,
        action=action,
        actor_id=actor_id,
        metadata_json=json.dumps(metadata)
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
