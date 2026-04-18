import redis
import json
import os
import time
import sys

def main():
    print("🚀 Event Pipeline Worker Started...")
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))

    try:
        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=0,
            socket_timeout=5
        )
        redis_client.ping()
        print(f"Connected to Redis at {redis_host}:{redis_port}")
    except Exception as e:
        print(f"REDIS ERROR: Could not connect to {redis_host}:{redis_port}: {e}")
        print("REDIS: not available, event worker exiting")
        sys.exit(0)

    pubsub = redis_client.pubsub()
    pubsub.subscribe(["procurement.events", "vision.events", "audit.events"])

    print("Listening for events...")
    try:
        for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                topic = message['channel'].decode()
                print(f" [EVENT] Topic: {topic} | Data: {data}")
    except KeyboardInterrupt:
        print("Worker stopping...")

if __name__ == "__main__":
    main()
