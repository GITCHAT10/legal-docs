import redis
import json
import os
import time

def main():
    print("🚀 Event Pipeline Worker Started...")
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=0
    )

    pubsub = redis_client.pubsub()
    pubsub.subscribe(["procurement.events", "vision.events", "audit.events"])

    for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'])
            topic = message['channel'].decode()
            print(f" [EVENT] Topic: {topic} | Data: {data}")
            # Here we would persist to Shadow ledger or SAL
            # For blueprint, we log to stdout as verification

if __name__ == "__main__":
    main()
