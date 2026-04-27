import contextvars
from typing import Optional, Dict, Any

_audit_context = contextvars.ContextVar("audit_context", default=None)

def set_audit_context(identity_id: str, device_id: str, trace_id: str):
    _audit_context.set({
        "identity_id": identity_id,
        "device_id": device_id,
        "trace_id": trace_id
    })

def get_audit_context() -> Optional[Dict[str, Any]]:
    return _audit_context.get()

def clear_audit_context():
    _audit_context.set(None)
