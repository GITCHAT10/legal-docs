from datetime import datetime, UTC
import uuid

def emit_settlement_event(status, payload, actor=None, context=None, proof=None):
    """
    Emits a schema-complete MNOS v1.1 FCE settlement event.
    """
    event_id = str(uuid.uuid4())

    # Minimum safe default actor
    if actor is None:
        actor = {
            "id": "fce_settlement_engine",
            "role": "SYSTEM.FCE.SETTLEMENT"
        }

    # Minimum safe default context
    if context is None:
        context = {
            "workflow_id": payload.get("workflow_id", str(uuid.uuid4())),
            "correlation_id": payload.get("correlation_id", str(uuid.uuid4())),
            "tenant": payload.get("tenant", {
                "brand": "SALA",
                "tin": "SALA-MV-2026-STAGING",
                "jurisdiction": "MV"
            })
        }

    # Minimum safe default proof
    if proof is None:
        proof = {
            "signature": f"SIG-{uuid.uuid4().hex[:8]}",
            "algorithm": "ED25519",
            "public_key_id": "key_fce_system",
            "shadow_chain_ref": payload.get("shadow_ref", "NONE"),
            "fce_settlement_ref": payload.get("settlement_id", "NONE")
        }

    return {
        "event_id": event_id,
        "event_type": f"FCE.SETTLEMENT.{status}",
        "timestamp": datetime.now(UTC).isoformat(),
        "source": { "system": "CORE" },
        "actor": actor,
        "context": context,
        "payload": payload,
        "proof": proof,
        "metadata": { "schema_version": "1.1" }
    }
