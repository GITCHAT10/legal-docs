import redis
import json
import os
import time
import sys
import httpx
import asyncio

SAL_URL = os.getenv("SAL_URL", "http://sal:8004")

async def log_to_sal(data):
    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"{SAL_URL}/log", json=data)
            print(f" [SAL] Logged: {data.get('event', 'unknown')}")
        except Exception as e:
            print(f" [SAL] Error: {e}")

async def main():
    print("🚀 MNOS Event Pipeline Worker Starting...")
    redis_host = os.getenv("REDIS_HOST", "localhost")

    # Strict Redis Connection
    try:
        redis_client = redis.Redis(host=redis_host, port=6379, db=0, socket_timeout=5)
        redis_client.ping()
        print(f"✅ Connected to Redis at {redis_host}")
    except Exception as e:
        print(f"❌ CRITICAL REDIS ERROR: {e}")
        sys.exit(1) # Fail loudly

    pubsub = redis_client.pubsub()
    pubsub.subscribe(["procurement.events", "audit.events", "module.events"])

    print("✅ Subscribed. Listening for MNOS events...")

    while True:
        try:
            message = pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                data = json.loads(message['data'])
                await log_to_sal(data)
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Worker Loop Error: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
