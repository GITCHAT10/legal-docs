import json
import time
import os

class MockRedis:
    def __init__(self, *args, **kwargs):
        self.file_path = "mock_redis_bus.jsonl"
        # Ensure file exists
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                pass

    def publish(self, channel, message):
        with open(self.file_path, "a") as f:
            f.write(json.dumps({"channel": channel, "data": message}) + "\n")

    def pubsub(self):
        return MockPubSub(self)

class MockPubSub:
    def __init__(self, redis):
        self.redis = redis
        self.subscribed_channels = []
        self.last_pos = 0

    def subscribe(self, *channels):
        self.subscribed_channels = list(channels)
        # Start from the end of the file to only get new messages
        if os.path.exists(self.redis.file_path):
            self.last_pos = os.path.getsize(self.redis.file_path)

    def listen(self):
        while True:
            if not os.path.exists(self.redis.file_path):
                time.sleep(0.1)
                continue

            with open(self.redis.file_path, "r") as f:
                f.seek(self.last_pos)
                line = f.readline()
                if line:
                    self.last_pos = f.tell()
                    msg = json.loads(line)
                    if msg["channel"] in self.subscribed_channels:
                        yield {"type": "message", "channel": msg["channel"], "data": msg["data"]}
                else:
                    time.sleep(0.1)

shared_redis = MockRedis()

def get_redis_client(*args, **kwargs):
    return shared_redis
