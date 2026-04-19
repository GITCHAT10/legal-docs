import hashlib
import hmac
import json
import os
from mnos.database import SessionLocal, ShadowLogModel
from datetime import datetime
import uuid

SECRET_KEY = os.getenv("MNOS_INTEGRATION_SECRET", "dev_fallback_secret")

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

            # Generate Cryptographic Signature for Sovereign Audit
            data_to_sign = f"{prev_hash}:{event_type}:{payload_str}:{entry_id}:{curr_hash}"
            signature = hmac.new(SECRET_KEY.encode(), data_to_sign.encode(), hashlib.sha256).hexdigest()

            new_log = ShadowLogModel(
                id=entry_id,
                event_type=event_type,
                payload={**payload, "mnos_signature": signature},
                previous_hash=prev_hash,
                current_hash=curr_hash
            )
            db.add(new_log)
            db.commit()
            return curr_hash
        finally:
            db.close()
