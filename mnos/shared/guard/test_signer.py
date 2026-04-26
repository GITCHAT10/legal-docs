import hmac
import hashlib
from mnos.core.apollo.registry import apollo_registry

def aegis_sign(payload):
    """Authoritative test helper for signing requests against the Apollo Registry."""
    user_id = payload.get("user_id")
    node_id = apollo_registry._user_node_map.get(user_id)
    if not node_id:
        return "invalid_sig"

    node = apollo_registry._nodes.get(node_id)
    if not node:
        return "invalid_node_sig"

    msg = f"{payload.get('nonce')}|{payload.get('issued_at')}|{payload.get('user_id')}|{payload.get('session_id')}".encode()
    return hmac.new(node.public_key.encode(), msg, hashlib.sha256).hexdigest()
