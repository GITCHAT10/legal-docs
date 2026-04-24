from sqlalchemy.orm import Session
from .models import IntegrationOutboxModel
from .service import generate_canonical_string, sign_payload_canonical, SECRET_KEY
from .logging_utils import logger
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import uuid
import os
import json
from datetime import datetime, timezone, timedelta

MNOS_URL = os.getenv("MNOS_URL", "http://localhost:8000")

session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[408, 502, 503, 504],
    allowed_methods=["POST"]
)
session.mount("http://", HTTPAdapter(max_retries=retry_strategy))

metrics = {
    "success_count": 0,
    "failure_count": 0,
    "retry_count": 0,
    "dead_letter_count": 0,
    "last_processed_at": None
}

def process_outbox(db: Session):
    now = datetime.utcnow()
    pending_events = db.query(IntegrationOutboxModel).filter(
        IntegrationOutboxModel.status.in_(["pending", "failed"]),
        IntegrationOutboxModel.next_attempt_at <= now,
        IntegrationOutboxModel.attempt_count < 4
    ).all()

    for entry in pending_events:
        try:
            method = "POST"
            path = "/integration/v1/events/production"
            timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
            request_id = str(uuid.uuid4())
            correlation_id = entry.payload_json.get("correlation_id") or str(uuid.uuid4())

            body_json = json.dumps(entry.payload_json, sort_keys=True)
            body_bytes = body_json.encode()

            canonical = generate_canonical_string(method, path, timestamp, request_id, body_bytes)
            signature = sign_payload_canonical(canonical, SECRET_KEY)

            headers = {
                "X-Request-Id": request_id,
                "X-Idempotency-Key": entry.idempotency_key,
                "X-Correlation-Id": correlation_id,
                "X-Timestamp": timestamp,
                "X-Signature": signature,
                "Content-Type": "application/json"
            }

            resp = session.post(f"{MNOS_URL}{path}", data=body_bytes, headers=headers, timeout=5)

            if 200 <= resp.status_code < 300:
                entry.status = "sent"
                metrics["success_count"] += 1
            else:
                handle_failure(entry, f"MNOS Error: {resp.status_code}")
                metrics["failure_count"] += 1

            entry.attempt_count += 1
            db.commit()
        except Exception as e:
            handle_failure(entry, f"Error: {str(e)}")
            db.commit()

def handle_failure(entry, error_msg):
    entry.status = "failed"
    entry.last_error = error_msg
    backoffs = [15, 60, 300]
    if entry.attempt_count < len(backoffs):
        entry.next_attempt_at = datetime.utcnow() + timedelta(seconds=backoffs[entry.attempt_count])
    else:
        metrics["dead_letter_count"] += 1

def get_metrics():
    return metrics
