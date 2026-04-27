import hmac
import hashlib
from .schemas import EmailEvent

class MailchimpAdapter:
    def __init__(self, api_key: str, webhook_secret: str):
        self.api_key = api_key
        self.webhook_secret = webhook_secret

    def send_campaign(self, campaign_name: str, recipients: list):
        print(f"[MAILCHIMP] Sending campaign '{campaign_name}' to {len(recipients)} recipients.")
        return {"status": "success", "campaign_id": "mc_123"}

    def validate_webhook(self, signature: str, raw_payload: bytes) -> bool:
        expected = hmac.new(self.webhook_secret.encode(), raw_payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def normalize_event(self, raw_data: dict) -> EmailEvent:
        return EmailEvent(
            email=raw_data.get("email"),
            event=raw_data.get("event"),
            campaign=raw_data.get("campaign"),
            timestamp=raw_data.get("timestamp")
        )
