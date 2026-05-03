from datetime import datetime, UTC
import uuid

def record_audit_event(ledger, event_type, actor_id, payload):
    """
    Records a schema-complete audit event in SHADOW.
    """
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "timestamp": datetime.now(UTC).isoformat(),
        "source": { "system": "CORE" },
        "actor": {"id": actor_id, "role": "AUDITOR"},
        "context": {
             "tenant": {
                 "brand": "MNOS",
                 "tin": "SYSTEM",
                 "jurisdiction": "CORE"
             }
        },
        "payload": payload,
        "proof": {
            "signature": "SYSTEM_AUDIT_SEAL",
            "algorithm": "INTERNAL"
        },
        "metadata": { "schema_version": "1.1" }
    }
    return ledger.commit(event)
