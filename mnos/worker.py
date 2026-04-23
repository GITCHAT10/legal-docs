try:
    import redis
    has_redis = True
except ImportError:
    has_redis = False

import json
import os
import hmac
import hashlib
from mnos.decision_engine import AegisPolicyEngine, FinancialControlEngine
from mnos.shadow_service import ShadowService
from mnos.security import SECRET_KEY
from mnos.events.publisher import EventPublisher

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

class EventWorker:
    def __init__(self):
        if has_redis:
            try:
                self.redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
                self.redis.ping()
            except:
                from mnos.mock_redis import get_redis_client
                self.redis = get_redis_client()
        else:
            from mnos.mock_redis import get_redis_client
            self.redis = get_redis_client()
        self.pubsub = self.redis.pubsub()

    def sign_decision(self, decision_payload: dict) -> str:
        message = json.dumps(decision_payload, sort_keys=True)
        return hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).hexdigest()

    def run(self):
        print("🚀 MNOS EVENT WORKER STARTING...")
        self.pubsub.subscribe("FUEL_REQUESTED")

        for message in self.pubsub.listen():
            if message["type"] == "message":
                # Standard Sovereign Event Handling
                event = json.loads(message["data"])
                data = event.get("payload", {})

                request_id = data.get("request_id")
                fuel_request = data.get("fuel_request")

                if not request_id or not fuel_request:
                    print(f"[!] Invalid Event Format: {event.get('id')}")
                    continue

                print(f"[*] Processing Fuel Request: {request_id}")

                # 1. AEGIS Policy Check (Hardened)
                try:
                    aegis_ok, aegis_msg = AegisPolicyEngine.validate_request(fuel_request)
                except PermissionError as e:
                    aegis_ok, aegis_msg = False, str(e)
                except Exception as e:
                    aegis_ok, aegis_msg = False, f"System Error: {str(e)}"

                # 2. FCE Financial Check
                fce_ok, fce_msg = (True, "Skipped")
                if aegis_ok:
                    fce_ok, fce_msg = FinancialControlEngine.check_clearance(fuel_request)

                decision = "APPROVE" if (aegis_ok and fce_ok) else "DENY"
                reason = aegis_msg if not aegis_ok else fce_msg

                decision_payload = {
                    "request_id": request_id,
                    "decision": decision,
                    "reason": reason
                }

                # 3. Sign Decision
                signature = self.sign_decision(decision_payload)
                final_payload = {
                    **decision_payload,
                    "mnos_signature": signature
                }

                # 4. Log to Shadow
                shadow_hash = ShadowService.log_event("DECISION_MADE", final_payload)
                final_payload["shadow_hash"] = shadow_hash

                # 5. Publish Decision via Standard Event Publisher
                channel = "FUEL_APPROVED" if decision == "APPROVE" else "FUEL_DENIED"

                # Emit Standard MNOS Event
                EventPublisher().publish(
                    channel=channel,
                    entity_id=fuel_request.get("aircraft_id", "UNKNOWN"),
                    entity_type="AIRCRAFT",
                    action="FUEL_CLEARANCE",
                    payload=final_payload
                )

                print(f"[DECISION: {decision}] Reason: {reason}")

if __name__ == "__main__":
    worker = EventWorker()
    worker.run()
