try:
    import redis
    has_redis = True
except ImportError:
    has_redis = False

import json
import os
import hmac
import hashlib

# These would ideally be shared or fetched from a secure source
MNOS_INTEGRATION_SECRET = os.getenv("MNOS_INTEGRATION_SECRET", "dev_fallback_secret")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

def control_fuel_valve(state):
    if state == "ON":
        print("FUEL FLOW: ACTIVE")
    else:
        print("FUEL FLOW: BLOCKED")

class EdgeFuelController:
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

    def verify_mnos_signature(self, payload: dict) -> bool:
        signature = payload.pop("mnos_signature", None)
        # remove shadow_hash if present as it was added after signing in worker
        shadow_hash = payload.pop("shadow_hash", None)

        message = json.dumps(payload, sort_keys=True)
        expected_signature = hmac.new(MNOS_INTEGRATION_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()

        # Put them back for logging
        if signature: payload["mnos_signature"] = signature
        if shadow_hash: payload["shadow_hash"] = shadow_hash

        return hmac.compare_digest(signature, expected_signature) if signature else False

    def run(self):
        print("🔌 EDGE NODE FUEL CONTROLLER STARTING...")
        self.pubsub.subscribe("FUEL_APPROVED", "FUEL_DENIED")

        # Default safety state
        control_fuel_valve("OFF")

        for message in self.pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                request_id = data.get("request_id")

                print(f"[*] Received Decision for Request: {request_id}")

                if self.verify_mnos_signature(data):
                    decision = data.get("decision")
                    if decision == "APPROVE":
                        print(f"[EDGE ACTION: FUEL FLOW ACTIVE] Request: {request_id}")
                        control_fuel_valve("ON")
                    else:
                        print(f"[EDGE ACTION: FUEL FLOW BLOCKED] Request: {request_id} (Reason: {data.get('reason')})")
                        control_fuel_valve("OFF")

                    # Log action back to shadow (via event or direct, here we print as requested)
                    print(f"[SHADOW HASH: {data.get('shadow_hash')}]")
                else:
                    print(f"⚠️  CRITICAL: INVALID MNOS SIGNATURE FOR REQUEST {request_id}")
                    control_fuel_valve("OFF")

if __name__ == "__main__":
    controller = EdgeFuelController()
    controller.run()
