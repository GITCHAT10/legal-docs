from collections import defaultdict
from datetime import datetime, UTC
import json
import uuid
import os

class DistributedEventBus:
    """
    Kafka-style Distributed Event Bus for MNOS N-DEOS.
    Partitioned by Island/Atoll. Durable and Replayable.
    """
    def __init__(self):
        self.partitions = defaultdict(list) # partition_key -> events[]
        self.offsets = defaultdict(int)     # consumer_id:partition -> offset
        self.storage_dir = "mnos/modules/events/storage"
        self.subscribers = defaultdict(list)
        os.makedirs(self.storage_dir, exist_ok=True)

    def subscribe(self, event_pattern: str, callback):
        """Subscribe to events matching a pattern (e.g., '*' for all)."""
        self.subscribers[event_pattern].append(callback)

    def publish(self, event_type: str, payload: dict, partition: str = "GLOBAL"):
        # SECURITY: Enforcement of ExecutionGuard Authority
        from mnos.shared.execution_guard import ExecutionGuard
        if not ExecutionGuard.is_authorized():
             raise PermissionError(f"FAIL CLOSED: Unauthorized direct publish of {event_type} blocked.")

        event_id = str(uuid.uuid4())
        event = {
            "id": event_id,
            "type": event_type,
            "payload": payload,
            "partition": partition,
            "timestamp": datetime.now(UTC).isoformat(),
            "trace_id": uuid.uuid4().hex[:8]
        }

        # 1. Append to in-memory partition
        self.partitions[partition].append(event)

        # 2. Durable storage (Simulated append-only log)
        self._persist_event(event)

        # 3. Notify synchronous subscribers
        for pattern, callbacks in self.subscribers.items():
            if pattern == "*" or pattern == event_type:
                for cb in callbacks:
                    try:
                        cb(event_type, payload)
                    except Exception as e:
                        print(f"[ERROR] Subscriber failed for {event_type}: {e}")

        print(f"[STREAM] {event_type} published to {partition} (ID: {event_id[:8]})")
        return event_id

    def _persist_event(self, event):
        path = os.path.join(self.storage_dir, f"partition_{event['partition']}.log")
        with open(path, "a") as f:
            f.write(json.dumps(event) + "\n")

    def consume(self, partition: str, consumer_id: str, callback):
        """Consume events from a specific partition and track offsets."""
        key = f"{consumer_id}:{partition}"
        start_index = self.offsets[key]
        events_to_process = self.partitions[partition][start_index:]

        for event in events_to_process:
            try:
                callback(event)
                self.offsets[key] += 1
            except Exception as e:
                print(f"[RECOVERY] Event {event['id']} processing failed: {e}")

    def replay_partition(self, partition: str, start_time: str = None):
        """Replay events for a partition, optionally from a specific time."""
        if not start_time:
            return self.partitions[partition]
        return [e for e in self.partitions[partition] if e["timestamp"] >= start_time]

    def recover_from_disk(self):
        """Recover state from durable logs (durability check)."""
        if not os.path.exists(self.storage_dir):
            return
        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".log"):
                partition = filename.replace("partition_", "").replace(".log", "")
                with open(os.path.join(self.storage_dir, filename), "r") as f:
                    for line in f:
                        event = json.loads(line.strip())
                        if event not in self.partitions[partition]:
                            self.partitions[partition].append(event)
        print("MNOS EVENT BUS: Recovery complete.")
