from sqlalchemy.orm import Session
from .models import IntegrationOutboxModel
from .service import generate_canonical_string, sign_payload_canonical, SECRET_KEY
import requests
import uuid
import os
import json
from datetime import datetime, timezone

MNOS_URL = os.getenv("MNOS_URL", "http://localhost:8000")

def process_outbox(db: Session):
    """Simple synchronous outbox processor for MVP/Sprint 1"""
    pending_events = db.query(IntegrationOutboxModel).filter(IntegrationOutboxModel.status == "pending").all()

    for entry in pending_events:
        try:
            method = "POST"
            path = "/mnos/integration/v1/events"
            timestamp = datetime.now(timezone.utc).isoformat()
            request_id = str(uuid.uuid4())

            # Use canonical signing format
            canonical = generate_canonical_string(method, path, timestamp, request_id, entry.payload_json)
            signature = sign_payload_canonical(canonical, SECRET_KEY)

            headers = {
                "X-Request-Id": request_id,
                "X-Idempotency-Key": entry.idempotency_key,
                "X-Timestamp": timestamp,
                "X-Signature": signature,
                "Content-Type": "application/json"
            }

            resp = requests.post(f"{MNOS_URL}{path}", json=entry.payload_json, headers=headers, timeout=(2, 5))

            if 200 <= resp.status_code < 300:
                entry.status = "sent"
            else:
                entry.status = "failed"
                entry.last_error = f"MNOS Error: {resp.status_code} - {resp.text}"

            entry.attempt_count += 1
            db.commit()
        except Exception as e:
            entry.status = "failed"
            entry.last_error = str(e)
            entry.attempt_count += 1
            db.commit()

def run_worker_loop(db_session_factory):
    """Conceptual loop for a real worker process"""
    import time
    while True:
        db = db_session_factory()
        try:
            process_outbox(db)
        finally:
            db.close()
        time.sleep(10)
