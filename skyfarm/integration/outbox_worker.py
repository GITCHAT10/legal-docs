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

# Internal metrics store (In a real app, use Prometheus/Redis)
metrics = {
    "success_count": 0,
    "failure_count": 0,
    "retry_count": 0,
    "dead_letter_count": 0,
    "last_processed_at": None
}

def process_outbox(db: Session):
    """Outbox processor with retry backoff and dead-letter system"""
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

            # Use exact body bytes for signing and transmission
            body_json = json.dumps(entry.payload_json, sort_keys=True)
            body_bytes = body_json.encode()

            # Use canonical signing format
            canonical = generate_canonical_string(method, path, timestamp, request_id, body_bytes)
            signature = sign_payload_canonical(canonical, SECRET_KEY)

            headers = {
                "X-Request-Id": request_id,
                "X-Idempotency-Key": entry.idempotency_key,
                "X-Timestamp": timestamp,
                "X-Signature": signature,
                "Content-Type": "application/json"
            }

            logger.info(f"Attempting to send event {event_id} to MNOS", extra={
                "event_id": event_id,
                "request_id": request_id,
                "attempt": entry.attempt_count + 1
            })

            if entry.attempt_count > 0:
                metrics["retry_count"] += 1

            resp = requests.post(f"{MNOS_URL}{path}", data=body_bytes, headers=headers, timeout=(2, 5))

            if 200 <= resp.status_code < 300:
                entry.status = "sent"
                metrics["success_count"] += 1
                logger.info(f"Event {event_id} successfully sent to MNOS", extra={
                    "event_id": event_id,
                    "request_id": request_id
                })
            else:
                error_msg = f"MNOS Error: {resp.status_code} - {resp.text}"
                handle_failure(entry, error_msg)
                metrics["failure_count"] += 1
                logger.error(f"Event {event_id} failed to send to MNOS: {error_msg}", extra={
                    "event_id": event_id,
                    "request_id": request_id
                })

            entry.attempt_count += 1
            metrics["last_processed_at"] = datetime.now(timezone.utc).isoformat()
            db.commit()
        except Exception as e:
            handle_failure(entry, str(e))
            metrics["failure_count"] += 1
            logger.error(f"Error processing outbox event {event_id}: {str(e)}", extra={
                "event_id": event_id
            })
            entry.attempt_count += 1
            metrics["last_processed_at"] = datetime.now(timezone.utc).isoformat()
            db.commit()

def handle_failure(entry, error_msg):
    entry.status = "failed"
    entry.last_error = error_msg

    # Backoff logic: 15s, 60s, 5m, 15m
    backoffs = [15, 60, 300, 900]
    if entry.attempt_count < len(backoffs):
        entry.next_attempt_at = datetime.utcnow() + timedelta(seconds=backoffs[entry.attempt_count])
    else:
        entry.status = "dead_letter"
        metrics["dead_letter_count"] += 1
        logger.error(f"Event {entry.event_id} moved to DEAD LETTER QUEUE")

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
