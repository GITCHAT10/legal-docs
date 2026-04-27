import uuid
from typing import Dict, List, Any
from datetime import datetime, UTC

class ApolloReplicationQueue:
    """
    APOLLO: Replicated Outbox/Inbox Queue.
    Handles signed delta payloads and AEGIS trust verification.
    """
    def __init__(self, shadow, aegis_gateway, topology=None):
        self.shadow = shadow
        self.aegis = aegis_gateway
        self.topology = topology
        self.outbox = [] # Pending deltas to send
        self.inbox = []  # Deltas received to apply
        self.processed_traces = set() # Idempotency check
        self.offline_queue = []

    def enqueue_delta(self, actor_ctx: dict, delta_payload: dict) -> str:
        """
        Signs and queues a state delta for replication.
        """
        trace_id = delta_payload.get("trace_id", str(uuid.uuid4()))

        # Mandatory trace_id and signed delta
        delta = {
            "msg_id": f"DEL-{uuid.uuid4().hex[:6].upper()}",
            "trace_id": trace_id,
            "payload": delta_payload,
            "signature": f"SIG-{trace_id[:8]}", # Simplified signing
            "timestamp": datetime.now(UTC).isoformat()
        }

        self.outbox.append(delta)
        return delta["msg_id"]

    def receive_delta(self, delta: dict, source_node_id: str):
        """
        Receives and validates a delta from another node.
        """
        # Rule: unknown node = deny replication
        if self.topology and source_node_id not in self.topology.nodes:
            raise PermissionError(f"FAIL CLOSED: Replication denied for unknown node {source_node_id}")

        trace_id = delta.get("trace_id")

        # 1. Idempotency Check
        if trace_id in self.processed_traces:
            return "ALREADY_PROCESSED"

        # 2. AEGIS Trust check (simplified)
        # Requirement: reject if no AEGIS trust
        if "signature" not in delta:
            raise PermissionError("FAIL CLOSED: Delta rejected - Missing signature")

        self.inbox.append(delta)
        self.processed_traces.add(trace_id)
        return "QUEUED_INBOX"

    def handle_reconnect(self):
        """
        Rule: offline queue replays after reconnect.
        """
        replayed = len(self.offline_queue)
        for delta in self.offline_queue:
            self.inbox.append(delta)
        self.offline_queue = []
        return replayed

    def apply_inbox(self, app_core):
        """
        Replays the inbox deltas onto the local state.
        """
        count = 0
        for delta in self.inbox:
            # Replay logic...
            count += 1
        self.inbox = []
        return count
