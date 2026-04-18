import hashlib
import json
from mnos.database import SessionLocal, ShadowLogModel
from datetime import datetime
import uuid

class ShadowService:
    @staticmethod
    def log_event(event_type: str, payload: dict):
        db = SessionLocal()
        try:
            # Get last hash
            last_entry = db.query(ShadowLogModel).order_by(ShadowLogModel.timestamp.desc()).first()
            prev_hash = last_entry.current_hash if last_entry else "GENESIS_HASH"

            # Calculate current hash
            entry_id = str(uuid.uuid4())
            payload_str = json.dumps(payload, sort_keys=True)
            curr_hash = hashlib.sha256(f"{prev_hash}:{event_type}:{payload_str}:{entry_id}".encode()).hexdigest()

            new_log = ShadowLogModel(
                id=entry_id,
                event_type=event_type,
                payload=payload,
                previous_hash=prev_hash,
                current_hash=curr_hash
            )
            db.add(new_log)
            db.commit()
            return curr_hash
        finally:
            db.close()
