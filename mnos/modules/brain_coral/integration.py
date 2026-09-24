from datetime import UTC, datetime
from uuid import uuid4
from typing import Any, Dict

from mnos.shared.execution_guard import authorized_context


ALLOWED_REVIEW_TARGETS = {"ops.summary.review"}

RESTRICTED_MUTATION_TARGETS = {
    "finance.release",
    "finance.refund.approve",
    "finance.escrow.release",
    "procurement.approve",
    "procurement.order.settle",
    "room_inventory.change",
    "identity.create",
    "identity.role.assign",
    "settlement.post",
    "commerce.order.force_create",
}


class BrainCoralMnosBridge:
    """
    Governed integration layer between BRAIN CORAL, MAC EOS/iMOXON and MNOS.

    BRAIN CORAL is intelligence/orchestration only. It may read operational posture
    and submit action requests for human/governed review, but it must not directly
    mutate finance, procurement, rooms, identity, settlement, or commerce state.
    """

    def __init__(self, core, shadow, events):
        self.core = core
        self.shadow = shadow
        self.events = events
        self.action_requests: Dict[str, Dict[str, Any]] = {}

    def read_operational_status(self, actor_ctx: dict) -> dict:
        """Return a guarded, audited read-only status snapshot for BRAIN CORAL."""
        return self.core.execute_commerce_action(
            "brain_coral.operational.read",
            actor_ctx,
            self._read_operational_status,
        )

    def _read_operational_status(self) -> dict:
        snapshot = {
            "system": "BRAIN_CORAL_MNOS_BRIDGE",
            "mode": "READ_ONLY_INTELLIGENCE",
            "status": "CONNECTED",
            "mac_eos": {
                "shadow_integrity": self.shadow.verify_integrity(),
                "ledger_entries": len(self.shadow.chain),
            },
            "permissions": {
                "direct_finance_mutation": False,
                "direct_procurement_mutation": False,
                "direct_room_inventory_mutation": False,
                "direct_identity_mutation": False,
                "requires_execution_guard": True,
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.events.publish("brain_coral.operational_status.read", snapshot)
        return snapshot

    def request_governed_action(self, actor_ctx: dict, request_data: dict) -> dict:
        """
        Accept an intelligence action request without executing the underlying mutation.

        This is the safe BRAIN CORAL pattern: request, audit, and queue for an
        authorized human/system workflow rather than bypassing ExecutionGuard.
        """
        if not isinstance(request_data, dict) or not isinstance(request_data.get("target"), str) or not request_data["target"].strip():
            raise ValueError("non-empty target is required")
        return self.core.execute_commerce_action(
            "brain_coral.action.request",
            actor_ctx,
            self._request_governed_action,
            request_data,
        )

    def _request_governed_action(self, request_data: dict) -> dict:
        if not isinstance(request_data, dict):
            raise ValueError("request body must be an object")
        target = request_data.get("target")
        if not isinstance(target, str) or not target.strip():
            raise ValueError("non-empty target is required")
        target = target.strip()
        # Explicit review-only allowlist. Unknown action identifiers fail closed.
        if target not in ALLOWED_REVIEW_TARGETS:
            raise PermissionError(
                f"BRAIN CORAL read-only boundary: direct mutation blocked for {target}"
            )

        request_id = f"BC-REQ-{uuid4()}"
        record = {
            "request_id": request_id,
            "target": target,
            "intent": request_data.get("intent"),
            "payload": request_data.get("payload", {}),
            "status": "QUEUED_FOR_GOVERNED_REVIEW",
            "created_at": datetime.now(UTC).isoformat(),
        }
        self.action_requests[request_id] = record
        self.events.publish("brain_coral.action_request.queued", record)
        return record


class MNOSIntegrationHub:
    """
    Internal MNOS bridge for background syncs and operational heartbeat events.

    External actors must still use AEGIS headers and ExecutionGuard. This hub only
    uses authorized_context for legitimate internal system-owned sync operations.
    """

    def __init__(self, shadow, events):
        self.shadow = shadow
        self.events = events
        self.sync_log = []

    def sync_internal_state(self, source: str, payload: dict) -> dict:
        if not source:
            raise ValueError("source is required")

        actor = {
            "identity_id": "MNOS_SYSTEM",
            "device_id": "internal-mnos-sync",
            "role": "system",
            "realm": "INTERNAL",
            "verified": True,
            "national_id_verified": True,
        }
        record = {
            "source": source,
            "payload": payload,
            "status": "SYNCED",
            "synced_at": datetime.now(UTC).isoformat(),
        }
        with authorized_context(actor):
            self.shadow.commit("mnos.internal.sync.completed", actor["identity_id"], record)
            self.events.publish("mnos.internal.sync.completed", record, partition="MNOS")

        self.sync_log.append(record)
        return record
