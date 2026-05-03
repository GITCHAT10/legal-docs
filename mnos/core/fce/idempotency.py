import hashlib

def calculate_idempotency_key(tin: str, event_type: str, transaction_id: str, amount: float, currency: str, shadow_ref: str) -> str:
    """
    idempotency = sha256(tin|event_type|transaction_id|amount|currency|shadow_ref)
    """
    components = [
        str(tin),
        str(event_type),
        str(transaction_id),
        f"{amount:.2f}",
        str(currency),
        str(shadow_ref)
    ]
    raw = "|".join(components)
    return hashlib.sha256(raw.encode()).hexdigest()
