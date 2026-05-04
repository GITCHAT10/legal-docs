from fastapi import Request, HTTPException, Header
from typing import Optional

async def get_actor_context(
    request: Request,
    x_aegis_identity: Optional[str] = Header(None, alias="X-AEGIS-IDENTITY"),
    x_aegis_device: Optional[str] = Header(None, alias="X-AEGIS-DEVICE"),
    x_trace_id: Optional[str] = Header(None, alias="X-TRACE-ID")
):
    """
    Scoped Actor Context Dependency.
    Extracts AEGIS identity, device, and trace context.
    """
    # In a real implementation, we would validate these against the identity core
    # and verify signatures. For this scaffold, we enforce presence.

    if not x_aegis_identity:
        raise HTTPException(status_code=401, detail="AEGIS_AUTH_REQUIRED: Missing Identity")

    if not x_aegis_device:
        raise HTTPException(status_code=403, detail="AEGIS_DEVICE_REQUIRED: Missing Device Binding")

    # Mock role and organization lookup based on identity_id
    # In production, this comes from AegisIdentityCore
    actor = {
        "identity_id": x_aegis_identity,
        "device_id": x_aegis_device,
        "role": "authorized_user", # Default or looked up
        "organization_id": "MIG",   # Default or looked up
        "trace_id": x_trace_id or "GEN-" + x_aegis_identity[:4]
    }

    # Set sovereign context for shadow ledger commits if not already set
    from mnos.shared.execution_guard import _sovereign_context
    if not _sovereign_context.get():
        _sovereign_context.set({"token": "AUTO-TOKEN", "actor": actor})

    return actor
