import hashlib
import json
from sqlalchemy.orm import Session
from mnos.database import EventLogModel

def shadow_write_service(event: dict, db: Session):
    # Stabilize hash chaining: Hash is derived from event + last ingested event ID
    last_event = db.query(EventLogModel).order_by(EventLogModel.timestamp.desc()).first()
    prev_id = last_event.id if last_event else "GENESIS"

    event_json = json.dumps(event, sort_keys=True)
    chain_input = f"{prev_id}|{event_json}"
    shadow_hash = hashlib.sha256(chain_input.encode()).hexdigest()

    # We return the hash as the shadow_entry_id for stability
    return f"shd_{shadow_hash[:16]}"
