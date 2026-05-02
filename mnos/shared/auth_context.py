import contextvars
import uuid
from typing import Dict, Optional

# Absolute authority for context
_sovereign_context = contextvars.ContextVar("sovereign_context", default=None)

def set_sovereign_context(actor: Dict):
    return _sovereign_context.set({"token": str(uuid.uuid4()), "actor": actor})

def reset_sovereign_context(token):
    _sovereign_context.reset(token)

def is_sovereign_authorized() -> bool:
    return _sovereign_context.get() is not None

def get_sovereign_actor() -> Optional[Dict]:
    ctx = _sovereign_context.get()
    return ctx["actor"] if ctx else None
