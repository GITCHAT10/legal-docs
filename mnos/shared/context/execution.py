import contextvars
import uuid
from datetime import datetime, UTC
from typing import Optional

_trace_id_var = contextvars.ContextVar("trace_id", default=None)
_aegis_id_var = contextvars.ContextVar("aegis_id", default=None)
_device_id_var = contextvars.ContextVar("device_id", default=None)

def set_execution_context(aegis_id: str, device_id: str, trace_id: Optional[str] = None):
    if not trace_id:
        # User mandated: trace_id + aegis_id + device_id + timestamp
        ts = int(datetime.now(UTC).timestamp())
        trace_id = f"TR-{uuid.uuid4().hex[:6]}-{aegis_id}-{device_id}-{ts}"

    _trace_id_var.set(trace_id)
    _aegis_id_var.set(aegis_id)
    _device_id_var.set(device_id)
    return trace_id

def get_trace_id() -> Optional[str]:
    return _trace_id_var.get()

def get_aegis_id() -> Optional[str]:
    return _aegis_id_var.get()

def get_device_id() -> Optional[str]:
    return _device_id_var.get()
