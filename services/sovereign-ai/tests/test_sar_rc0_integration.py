from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.sar.authority import AuthorityLevel, DynamicAuthority, TrustState
from app.sar.failure_recovery import A17RecoveryHarness, TimeoutClass
from app.sar.tool_gate import CapabilityState, Ed25519ToolGate


def test_a11_trust_downgrade_evicts_capability_and_never_auto_restores():
    private = Ed25519PrivateKey.generate()
    state = CapabilityState()
    state.current_policy_hash = "p1"
    state.active_agents.add("agent-1")
    state.asset_authority["vessel-1"] = {"dispatch"}
    gate = Ed25519ToolGate(private.public_key(), state, clock=lambda: 1001)
    token = Ed25519ToolGate.issue(
        private,
        agent_id="agent-1",
        tool="dispatch",
        asset_id="vessel-1",
        parameters={"route": "A-B"},
        policy_hash="p1",
        ttl_seconds=5,
        issued_at=1000,
    )

    authority = DynamicAuthority("agent-1")
    assert authority.apply_trust(TrustState.DEGRADED) == AuthorityLevel.A1
    state.revoke_agent("agent-1")  # capability eviction is immediate and beats TTL
    denied = gate.authorize(token, tool="dispatch", asset_id="vessel-1", parameters={"route": "A-B"})
    assert denied.allowed is False

    assert authority.apply_trust(TrustState.TRUSTED) == AuthorityLevel.A1
    assert authority.restoration_required is True


def test_x0_quarantine_forces_a0_and_zero_effect_denial():
    authority = DynamicAuthority("agent-1")
    authority.x0_quarantine("payments")
    assert authority.authority == AuthorityLevel.A0
    assert "payments" in authority.quarantined_domains
    assert authority.restoration_required is True


def test_a17_post_effect_loss_requires_verify_before_any_retry():
    h = A17RecoveryHarness()
    initial = h.classify(TimeoutClass.POST_EFFECT_RESPONSE_LOSS)
    assert initial.retry is False
    assert initial.verify_effect is True
    verified = h.recover_unknown(lambda: True, retry_count=0)
    assert verified.retry is False
    assert verified.reason == "DO_NOT_RETRY_EFFECT_EXISTS"
