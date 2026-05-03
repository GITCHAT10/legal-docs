
def record_audit_event(ledger, event_type, actor_id, payload):
    event = {
        "event_type": event_type,
        "actor": {"id": actor_id, "role": "AUDITOR"},
        "payload": payload,
        "timestamp": None # Ledger will set it if missing
    }
    return ledger.commit(event)
