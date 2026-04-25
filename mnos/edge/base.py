class EdgeNode:
    """
    N-DEOS Edge Node for Resorts/Atolls.
    Supports offline queueing and local execution fallback.
    """
    def __init__(self, island_id: str, events, guard):
        self.island_id = island_id
        self.events = events
        self.guard = guard
        self.offline_queue = []
        self.status = "ONLINE"

    def execute_local(self, action_type: str, actor_ctx: dict, func, *args, **kwargs):
        if self.status == "OFFLINE":
            print(f"[EDGE-{self.island_id}] Offline mode: Queueing {action_type}")
            self.offline_queue.append((action_type, actor_ctx, args, kwargs))
            return {"status": "QUEUED_OFFLINE"}

        # Local execution using standard guard
        return self.guard.execute_sovereign_action(action_type, actor_ctx, func, *args, **kwargs)

    def sync_to_core(self):
        print(f"[EDGE-{self.island_id}] Syncing {len(self.offline_queue)} events to core...")
        # Simulated sync
        self.offline_queue = []
        return True
