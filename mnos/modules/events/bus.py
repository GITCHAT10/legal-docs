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
        self.consumers = defaultdict(list)  # partition -> [(consumer_id, callback)]
        self.storage_dir = "mnos/modules/events/storage"
        os.makedirs(self.storage_dir, exist_ok=True)

    def publish(self, event_type: str, payload: dict, partition: str = "GLOBAL"):
        from mnos.shared.execution_guard import ExecutionGuard
        if not ExecutionGuard.is_authorized():
             # Bootstrap bypass for core events
             bootstrap_events = ["IDENTITY_CREATED", "IDENTITY_VERIFIED", "IDENTITY_DEVICE_BOUND"]
             if event_type not in bootstrap_events:
                raise PermissionError(f"FAIL CLOSED: Direct event publish blocked for {event_type}. Must use ExecutionGuard.")

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

        print(f"[STREAM] {event_type} published to {partition} (ID: {event_id[:8]})")

        # 3. Real-time consumption for sim
        for cid, callback in self.consumers[partition]:
             try:
                 callback(event)
                 self.offsets[f"{cid}:{partition}"] = len(self.partitions[partition])
             except Exception as e:
                 print(f"[STREAM-FAIL] Consumer {cid} failed: {e}")

        return event_id

    def _persist_event(self, event):
        path = os.path.join(self.storage_dir, f"partition_{event['partition']}.log")
        with open(path, "a") as f:
            f.write(json.dumps(event) + "\n")

    def consume(self, partition: str, consumer_id: str, callback):
        """Consume events from a specific partition and track offsets."""
        self.consumers[partition].append((consumer_id, callback))

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
