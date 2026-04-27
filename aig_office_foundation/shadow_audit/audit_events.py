from datetime import datetime, UTC

def create_audit_event(event_type: str, actor_id: str, device_id: str, trace_id: str, payload: dict) -> dict:
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "event_type": event_type,
        "actor_id": actor_id,
        "device_id": device_id,
        "trace_id": trace_id,
        "payload": payload
    }
