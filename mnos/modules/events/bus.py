class DistributedEventBus:
    """
    N-DEOS Distributed Event Streaming Core.
    Handles partitioned event publishing with court-grade replay capability.
    """
    def __init__(self):
        self.partitions = {
            "GLOBAL": [],
            "MALE": [],
            "RESORT": [],
            "PORT": []
        }

    def publish(self, event_type: str, payload: dict, partition: str = "GLOBAL"):
        from mnos.shared.execution_guard import ExecutionGuard

        ALLOWED_BOOTSTRAP_EVENTS = {
            "IDENTITY_CREATED",
            "SYSTEM_BOOTSTRAP"
        }

        if not ExecutionGuard.is_authorized():
             if event_type not in ALLOWED_BOOTSTRAP_EVENTS:
                 raise PermissionError(
                     f"FAIL CLOSED: Direct event publish blocked for {event_type}. Must use ExecutionGuard."
                 )

        event = {
            "type": event_type,
            "payload": payload,
            "partition": partition
        }
        if partition not in self.partitions:
            self.partitions[partition] = []
        self.partitions[partition].append(event)
        print(f"[STREAM] {event_type} published to {partition} (ID: {str(id(event))[:8]})")
        return True
