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
        self.redis.publish(channel, json.dumps(message))
