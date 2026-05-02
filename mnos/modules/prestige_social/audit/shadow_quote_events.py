import hashlib
import json
from datetime import datetime, UTC

def create_shadow_event(event_type: str, lead_id: str, actor_type: str, actor_id: str,
                        parent_hash: str, correlation_id: str, payload: dict,
                        quote_id: str = None, request_id: str = None,
                        content_id: str = None, campaign_id: str = None,
                        source_platform: str = None):

    timestamp = datetime.now(UTC).isoformat()

    event_data = {
        "event_type": event_type,
        "lead_id": lead_id,
        "quote_id": quote_id,
        "request_id": request_id,
        "actor_type": actor_type,
        "actor_id": actor_id,
        "timestamp": timestamp,
        "parent_hash": parent_hash,
        "correlation_id": correlation_id,
        "content_id": content_id,
        "campaign_id": campaign_id,
        "source_platform": source_platform,
        "payload_summary": payload
    }

    # Simple deterministic hash for MVP
    data_str = json.dumps(event_data, sort_keys=True)
    event_hash = f"sha256:{hashlib.sha256(data_str.encode()).hexdigest()}"

    event_data["hash"] = event_hash

    # In a real system, this would call shadow_core.commit()
    # For now, we return it for the bridge to use
    return event_data
