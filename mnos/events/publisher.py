try:
    import redis
    has_redis = True
except ImportError:
    has_redis = False

import json
import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

class EventPublisher:
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

    def publish(self, channel: str, message: dict):
        import time
        max_retries = 3
        retry_delay = 1 # second

        for attempt in range(max_retries):
            try:
                self.redis.publish(channel, json.dumps(message))
                return True
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"FAILED to publish to Redis after {max_retries} attempts: {str(e)}")
                    return False
                time.sleep(retry_delay * (2 ** attempt)) # Exponential backoff
