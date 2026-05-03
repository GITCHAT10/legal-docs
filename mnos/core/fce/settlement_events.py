from datetime import datetime, UTC
import uuid

def emit_settlement_event(status, payload):
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": f"FCE.SETTLEMENT.{status}",
        "timestamp": datetime.now(UTC).isoformat(),
        "source": { "system": "CORE" },
        "payload": payload,
        "metadata": { "schema_version": "1.1" }
    }
