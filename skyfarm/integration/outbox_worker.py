from sqlalchemy.orm import Session
from .models import IntegrationOutboxModel
from .service import generate_canonical_string, sign_payload_canonical, SECRET_KEY
from .logging_utils import logger
import requests
import uuid
import os
import json
from datetime import datetime, timezone, timedelta

MNOS_URL = os.getenv("MNOS_URL", "http://localhost:8000")

# Internal metrics store
metrics = {
    "success_count": 0,
    "failure_count": 0,
    "retry_count": 0,
    "dead_letter_count": 0,
    "last_processed_at": None
}

def process_outbox(db: Session):
    """Outbox processor with Phase 3 retry backoff and dead-letter system"""
    now = datetime.utcnow()
    pending_events = db.query(IntegrationOutboxModel).filter(
        IntegrationOutboxModel.status.in_(["pending", "failed"]),
        IntegrationOutboxModel.next_attempt_at <= now,
        IntegrationOutboxModel.attempt_count < 4
    ).all()

    for entry in pending_events:
        event_id = entry.event_id
        try:
            method = "POST"
            path = "/mnos/integration/v1/events"
            timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
            request_id = str(uuid.uuid4())

            body_json = json.dumps(entry.payload_json, sort_keys=True)
            body_bytes = body_json.encode()

            canonical = generate_canonical_string(method, path, timestamp, request_id, body_bytes)
            signature = sign_payload_canonical(canonical, SECRET_KEY)

            headers = {
                "X-Request-Id": request_id,
                "X-Idempotency-Key": entry.idempotency_key,
                "X-Timestamp": timestamp,
                "X-Signature": signature,
                "Content-Type": "application/json"
            }

            if entry.attempt_count > 0:
                metrics["retry_count"] += 1

            # Phase 2: Timeouts
            resp = requests.post(f"{MNOS_URL}{path}", data=body_bytes, headers=headers, timeout=(2, 5))

            if 200 <= resp.status_code < 300:
                entry.status = "sent"
                metrics["success_count"] += 1
            else:
                # Phase 3: Handle Retryable vs Non-Retryable
                # Retry on: 408, 429, 5xx, timeout
                if resp.status_code in [408, 429] or resp.status_code >= 500:
                     error_msg = f"Retryable MNOS Error: {resp.status_code}"
                     handle_failure(entry, error_msg)
                else:
                     # Non-retryable (400, 401, 403, 409, 422) -> Move to DLQ immediately or just fail
                     entry.status = "failed"
                     entry.last_error = f"Permanent MNOS Error: {resp.status_code} - {resp.text}"

                metrics["failure_count"] += 1

            entry.attempt_count += 1
            metrics["last_processed_at"] = datetime.now(timezone.utc).isoformat()
            db.commit()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            handle_failure(entry, f"Network/Timeout Error: {str(e)}")
            metrics["failure_count"] += 1
            entry.attempt_count += 1
            db.commit()
        except Exception as e:
            entry.status = "failed"
            entry.last_error = f"System Error: {str(e)}"
            metrics["failure_count"] += 1
            entry.attempt_count += 1
            db.commit()

def handle_failure(entry, error_msg):
    entry.status = "failed"
    entry.last_error = error_msg

    # Phase 3: Exponential backoff (15s, 1m, 5m, 15m)
    backoffs = [15, 60, 300, 900]
    if entry.attempt_count < len(backoffs):
        entry.next_attempt_at = datetime.utcnow() + timedelta(seconds=backoffs[entry.attempt_count])
    else:
        entry.status = "dead_letter"
        metrics["dead_letter_count"] += 1

def run_worker_loop(db_session_factory):
    import time
    while True:
        db = db_session_factory()
        try:
            process_outbox(db)
        finally:
            db.close()
        time.sleep(10)

def get_metrics():
    return metrics
