from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.sar.tool_gate import CapabilityState, Ed25519ToolGate


def build_gate(now=1000):
    private = Ed25519PrivateKey.generate()
    state = CapabilityState()
    state.current_policy_hash = "policy-v1"
    state.active_agents.add("agent-1")
    state.asset_authority["asset-1"] = {"transfer.quote"}
    gate = Ed25519ToolGate(private.public_key(), state, clock=lambda: now)
    return private, state, gate


def issue(private, *, now=1000, params=None):
    return Ed25519ToolGate.issue(
        private,
        agent_id="agent-1",
        tool="transfer.quote",
        asset_id="asset-1",
        parameters=params or {"amount": "10.00"},
        policy_hash="policy-v1",
        ttl_seconds=5,
        issued_at=now,
    )


def test_valid_capability_is_single_use():
    private, _, gate = build_gate()
    token = issue(private)
    params = {"amount": "10.00"}
    assert gate.authorize(token, tool="transfer.quote", asset_id="asset-1", parameters=params).allowed is True
    denied = gate.authorize(token, tool="transfer.quote", asset_id="asset-1", parameters=params)
    assert denied.allowed is False
    assert denied.reason == "NONCE_ALREADY_USED"


def test_parameter_binding_fails_closed():
    private, _, gate = build_gate()
    token = issue(private)
    decision = gate.authorize(token, tool="transfer.quote", asset_id="asset-1", parameters={"amount": "11.00"})
    assert decision.allowed is False
    assert decision.reason == "PARAMETER_HASH_MISMATCH"


def test_revocation_beats_ttl():
    private, state, gate = build_gate()
    token = issue(private)
    cap = gate.parse_and_verify(token)
    state.revoke_token(cap["jti"])
    decision = gate.authorize(token, tool="transfer.quote", asset_id="asset-1", parameters={"amount": "10.00"})
    assert decision.allowed is False
    assert decision.reason == "CAPABILITY_REVOKED"


def test_dynamic_agent_revocation_beats_ttl():
    private, state, gate = build_gate()
    token = issue(private)
    state.revoke_agent("agent-1")
    decision = gate.authorize(token, tool="transfer.quote", asset_id="asset-1", parameters={"amount": "10.00"})
    assert decision.allowed is False
    assert decision.reason == "AGENT_INACTIVE_OR_REVOKED"


def test_stale_policy_and_truth_dependency_deny():
    private, state, gate = build_gate()
    token = issue(private)
    state.current_policy_hash = "policy-v2"
    assert gate.authorize(token, tool="transfer.quote", asset_id="asset-1", parameters={"amount": "10.00"}).reason == "STALE_POLICY_HASH"

    private, state, gate = build_gate()
    state.truth_ok = lambda _: False
    token = issue(private)
    assert gate.authorize(token, tool="transfer.quote", asset_id="asset-1", parameters={"amount": "10.00"}).reason == "TRUTH_DEPENDENCY_UNACCEPTABLE"


def test_expiry_denies_with_zero_effect_semantics():
    private, _, _ = build_gate()
    token = issue(private)
    _, state, gate = build_gate(now=1005)
    # Use the original key's public key while preserving fresh runtime state.
    gate = Ed25519ToolGate(private.public_key(), state, clock=lambda: 1005)
    decision = gate.authorize(token, tool="transfer.quote", asset_id="asset-1", parameters={"amount": "10.00"})
    assert decision.allowed is False
    assert decision.reason == "EXPIRED_OR_NOT_YET_VALID"
