import hashlib

def risk_scoring_service(event: dict):
    # Deterministic scoring: Derived from tenant_id
    tenant_id = event.get("tenant_id", "unknown")
    score_hash = hashlib.md5(tenant_id.encode()).hexdigest()
    risk_score = (int(score_hash[:2], 16) % 100) / 100.0

    band = "LOW"
    if risk_score > 0.7:
        band = "HIGH"
    elif risk_score > 0.4:
        band = "MEDIUM"

    return {
        "risk_score": risk_score,
        "band": band
    }
