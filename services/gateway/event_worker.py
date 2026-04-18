import redis
import json
import os
import time
import sys
import httpx
import asyncio

def log_event(status, data, topic=None):
    print(json.dumps({
        "event_worker_status": status,
        "topic": topic,
        "data": data,
        "timestamp": time.time()
    }))

async def process_event(topic, data):
    log_event("event_received", data, topic)

    shadow_url = os.getenv("SHADOW_URL", "http://shadow:8000")

    # Simulate processing logic
    log_event("event_processed", data, topic)

    # Forward to SHADOW for immutable ledger commit
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{shadow_url}/entry", json=data, timeout=5.0)
            if resp.status_code == 200:
                log_event("event_committed", resp.json(), topic)
            else:
                log_event("event_commit_failed", {"status_code": resp.status_code}, topic)
        except Exception as e:
            log_event("event_commit_error", str(e), topic)

async def main():
    print("🚀 Event Pipeline Worker Starting...")
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))

    redis_client = None
    retry_count = 0
    while not redis_client:
        try:
            redis_client = redis.Redis(host=redis_host, port=redis_port, db=0, socket_timeout=5)
            redis_client.ping()
            print(f"✅ Connected to Redis at {redis_host}:{redis_port}")
        except Exception as e:
            retry_count += 1
            wait_time = min(2 ** retry_count, 30)
            print(f"⚠️ REDIS CONNECT FAILED ({retry_count}): {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)

    pubsub = redis_client.pubsub()
    pubsub.subscribe(["procurement.events", "vision.events", "audit.events"])

    print("✅ Subscribed to events. Listening...")

    while True:
        try:
            message = pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                topic = message['channel'].decode()
                data = json.loads(message['data'])
                await process_event(topic, data)
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Error in worker loop: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
