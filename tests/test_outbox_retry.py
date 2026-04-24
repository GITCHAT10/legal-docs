from sqlalchemy.orm import Session
from skyfarm.database import SessionLocal
from skyfarm.integration.models import IntegrationOutboxModel
from skyfarm.integration.outbox_worker import process_outbox, handle_failure
from datetime import datetime, timedelta
import responses
import os

@responses.activate
def test_outbox_retry_backoff():
    os.environ["ALLOW_INSECURE_DEV"] = "true"
    db = SessionLocal()
    try:
        # Create a failed entry
        entry = IntegrationOutboxModel(
            idempotency_key="retry_test_1",
            payload_json={"test": "data"},
            status="failed",
            attempt_count=1,
            next_attempt_at=datetime.utcnow() - timedelta(minutes=1)
        )
        db.add(entry)
        db.commit()

        # Mock MNOS failure (500)
        responses.add(
            responses.POST,
            "http://127.0.0.1:8000/integration/v1/events/production",
            json={"error": "Server Error"},
            status=500
        )

        process_outbox(db)

        db.refresh(entry)
        assert entry.status == "failed"
        assert entry.attempt_count == 2
        # Backoff for attempt 1 -> 2 is 60s
        assert entry.next_attempt_at > datetime.utcnow() + timedelta(seconds=50)

    finally:
        db.close()
