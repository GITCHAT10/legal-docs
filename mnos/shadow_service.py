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
            last_entry = db.query(ShadowLogModel).order_by(ShadowLogModel.timestamp.desc(), ShadowLogModel.id.desc()).first()
            prev_hash = last_entry.current_hash if last_entry else "GENESIS_HASH"

            # Calculate current hash
            entry_id = str(uuid.uuid4())
            # Canonical Payload for Hashing
            payload_str = json.dumps(payload, sort_keys=True)
            curr_hash = hashlib.sha256(f"{prev_hash}:{event_type}:{payload_str}:{entry_id}".encode()).hexdigest()

            # Generate Cryptographic Signature for Sovereign Audit
            # Signature covers the entire state including the current hash
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

    @staticmethod
    def verify_ledger_integrity() -> bool:
        """
        Audit the entire Shadow Ledger to ensure no tampering has occurred.
        """
        db = SessionLocal()
        try:
            entries = db.query(ShadowLogModel).order_by(ShadowLogModel.timestamp.asc(), ShadowLogModel.id.asc()).all()
            expected_prev_hash = "GENESIS_HASH"

            for entry in entries:
                # 1. Verify previous hash link
                if entry.previous_hash != expected_prev_hash:
                    return False

                # 2. Re-calculate hash
                payload_clean = {k: v for k, v in entry.payload.items() if k != "mnos_signature"}
                payload_str = json.dumps(payload_clean, sort_keys=True)
                actual_hash = hashlib.sha256(f"{entry.previous_hash}:{entry.event_type}:{payload_str}:{entry.id}".encode()).hexdigest()

                if actual_hash != entry.current_hash:
                    return False

                # 3. Verify Signature
                data_signed = f"{entry.previous_hash}:{entry.event_type}:{payload_str}:{entry.id}:{entry.current_hash}"
                expected_sig = hmac.new(SECRET_KEY.encode(), data_signed.encode(), hashlib.sha256).hexdigest()

                if not hmac.compare_digest(entry.payload.get("mnos_signature", ""), expected_sig):
                    return False

                expected_prev_hash = entry.current_hash

            return True
        finally:
            db.close()
