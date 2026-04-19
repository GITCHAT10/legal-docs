import logging
from mnos.shadow_service import ShadowService
from mnos.events.publisher import EventPublisher
import json

logger = logging.getLogger("unified_suite")

class SovereignFlows:
    # Set of locked resources to prevent unauthorized reuse after rejection
    _locked_resources = set()

    @classmethod
    def deny_flow(cls, resource_id: str, reason: str, context: dict):
        """
        Enforce rejection with cryptographic logs and resource locks.
        """
        event_payload = {
            "resource_id": resource_id,
            "action": "DENY",
            "reason": reason,
            "context": context
        }

        # 1. Cryptographic Log
        shadow_hash = ShadowService.log_event("SOVEREIGN_DENIAL", event_payload)

        # 2. Resource Lock
        cls._locked_resources.add(resource_id)

        # 3. Emit Enforcement Event
        EventPublisher().publish("enforcement.events", {**event_payload, "shadow_hash": shadow_hash})

        logger.error(f"Sovereign Denial: Resource {resource_id} locked. Reason: {reason}. Hash: {shadow_hash}")
        return {"status": "DENIED", "lock_id": shadow_hash[:8]}

    @classmethod
    def buffer_flow(cls, operation_type: str, payload: dict):
        """
        Offline island mode mechanism: Queue operations locally when central gateway is unreachable.
        """
        from datetime import datetime, timezone
        buffer_entry = {
            "operation": operation_type,
            "payload": payload,
            "buffered_at": datetime.now(timezone.utc).isoformat()
        }

        # In this simulation, we log it to a local 'buffer' (Shadow Ledger acts as local persistence)
        shadow_hash = ShadowService.log_event("BUFFERED_OFFLINE_OP", buffer_entry)

        logger.warning(f"Island Mode: Buffered {operation_type} for later sync. Hash: {shadow_hash}")
        return {"status": "BUFFERED", "sync_required": True, "buffer_hash": shadow_hash}

    @classmethod
    def replay_buffer(cls):
        """
        Replay all buffered operations to the central MNOS system.
        """
        from mnos.database import SessionLocal, ShadowLogModel
        db = SessionLocal()
        try:
            buffered_ops = db.query(ShadowLogModel).filter(ShadowLogModel.event_type == "BUFFERED_OFFLINE_OP").all()
            for op in buffered_ops:
                logger.info(f"Replaying operation: {op.payload.get('operation')}. Hash: {op.current_hash}")
                # Real implementation would call MNOS API here
            return len(buffered_ops)
        finally:
            db.close()

    @classmethod
    def is_resource_locked(cls, resource_id: str) -> bool:
        return resource_id in cls._locked_resources
