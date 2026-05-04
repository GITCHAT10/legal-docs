import time

def policy_evaluation_service(event: dict):
    # Deterministic policy: DENY if 'test_deny' is in data
    decision = "ALLOW"
    if event.get("data", {}).get("test_deny") is True:
        decision = "DENY"

    return {
        "decision": decision,
        "rules_evaluated": ["rule_default_allow", "rule_deny_check"],
        "latency_ms": 1.5 # Fixed latency for test stability
    }
