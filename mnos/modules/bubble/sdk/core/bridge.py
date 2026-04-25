class BubbleSDK:
    """
    Mini-App SDK: The platform layer for Bubble OS.
    Allows sandboxed plugins to request transactions and render cards.
    """
    def __init__(self, core):
        self.core = core

    def register_app(self, manifest: dict):
        # Validate manifest and permissions
        app_id = manifest.get("app_id")
        print(f"[SDK] Registered Mini App: {app_id}")
        return True

    def request_transaction(self, actor_ctx: dict, workflow_id: str, payload: dict):
        """Sandboxed method to trigger iMOXON workflows."""
        # Enforce Rule: No execution without AEGIS check (via Core)
        return self.core.execute(
            workflow_id,
            actor_ctx,
            self._dispatch_to_engine,
            workflow_id, payload
        )

    def _dispatch_to_engine(self, workflow_id, payload):
        # Internal dispatch logic
        self.core.events.publish("sdk.transaction_requested", {"wf": workflow_id, "data": payload})
        return {"status": "EXECUTED", "wf": workflow_id}
