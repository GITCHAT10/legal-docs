import requests
import json
import logging
from typing import Dict, Any

def emit_webhook(event_type: str, payload: Dict[str, Any], partner_webhook_url: str = None):
    """
    Dispatch webhooks to authorized partners.
    """
    if not partner_webhook_url:
        # Mock partner URL for sandbox
        partner_webhook_url = "https://partner-sandbox.unitedtransfer.mv/webhooks"

    logging.info(f"Emitting webhook {event_type} to {partner_webhook_url}")

    # In sandbox, we just log the dispatch
    dispatch_data = {
        "event": event_type,
        "timestamp": "2023-10-27T10:00:00Z", # Mock ISO
        "data": payload
    }

    print(f"WEBHOOK_DISPATCH: {json.dumps(dispatch_data)}")
    return True

def notify_safe_arrival(journey_id: int, leg_id: int):
    payload = {
        "journey_id": journey_id,
        "leg_id": leg_id,
        "status": "SAFE_ARRIVAL_CONFIRMED"
    }
    return emit_webhook("transfer.safe_arrival", payload)
