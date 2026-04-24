import uuid
import contextvars

_trace_id_ctx_var = contextvars.ContextVar("trace_id", default=None)

def get_trace_id() -> str:
    """Retrieves the current trace_id or generates a new one."""
    tid = _trace_id_ctx_var.get()
    if not tid:
        tid = str(uuid.uuid4())
        _trace_id_ctx_var.set(tid)
    return tid

def set_trace_id(tid: str):
    """Sets the trace_id for the current context."""
    _trace_id_ctx_var.set(tid)
