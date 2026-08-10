import pytest

from app.model_router import (
    AuthorityClass,
    ModelRouter,
    ModelTier,
    SecurityError,
)


def test_fast_route_stays_fast_within_token_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PII_EXTERNAL_PROCESSING_ALLOWED", raising=False)
    router = ModelRouter()
    decision = router.route_request(
        ModelTier.FAST.value,
        estimated_input_tokens=10_000,
        authority=AuthorityClass.CLASS_0,
    )
    assert decision.tier is ModelTier.FAST
    assert decision.requires_human_approval is False
    assert decision.permits_network_access is False
    assert decision.permits_production_write is False


def test_fast_route_promotes_when_token_boundary_exceeded() -> None:
    decision = ModelRouter().route_request(
        ModelTier.FAST.value,
        estimated_input_tokens=50_001,
        authority=AuthorityClass.CLASS_1,
    )
    assert decision.tier is ModelTier.BALANCED


def test_privileged_authority_forces_deep_and_hitl() -> None:
    decision = ModelRouter().route_request(
        ModelTier.FAST.value,
        estimated_input_tokens=1_000,
        authority=AuthorityClass.CLASS_3,
    )
    assert decision.tier is ModelTier.DEEP_REASONING
    assert decision.requires_human_approval is True


def test_pii_fails_closed_without_explicit_authorization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PII_EXTERNAL_PROCESSING_ALLOWED", raising=False)
    with pytest.raises(SecurityError, match="PII"):
        ModelRouter().route_request(
            ModelTier.BALANCED.value,
            estimated_input_tokens=1_000,
            authority=AuthorityClass.CLASS_1,
            payload_contains_pii=True,
        )


def test_pii_authorized_route_is_restricted_and_hitl(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PII_EXTERNAL_PROCESSING_ALLOWED", "TRUE")
    decision = ModelRouter().route_request(
        ModelTier.BALANCED.value,
        estimated_input_tokens=1_000,
        authority=AuthorityClass.CLASS_1,
        payload_contains_pii=True,
    )
    assert decision.tier is ModelTier.DEEP_REASONING
    assert decision.requires_human_approval is True
    assert decision.telemetry_classification == "RESTRICTED_METRICS_ONLY"


def test_ultra_guarded_fails_without_glasswing_and_enclave(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PROJECT_GLASSWING_ACCESS", raising=False)
    monkeypatch.delenv("MALDIVES_LOCAL_ENCLAVE", raising=False)
    with pytest.raises(SecurityError, match="Glasswing"):
        ModelRouter().route_request(
            ModelTier.ULTRA_GUARDED.value,
            estimated_input_tokens=1_000,
            authority=AuthorityClass.CLASS_2,
        )


def test_ultra_guarded_is_sandboxed_when_explicitly_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PROJECT_GLASSWING_ACCESS", "TRUE")
    monkeypatch.setenv("MALDIVES_LOCAL_ENCLAVE", "male-enclave-01")
    decision = ModelRouter().route_request(
        ModelTier.ULTRA_GUARDED.value,
        estimated_input_tokens=1_000,
        authority=AuthorityClass.CLASS_2,
    )
    assert decision.resolved_model_id == "claude-mythos-5"
    assert decision.containment_level == "SANDBOXED_NO_NET"
    assert decision.permits_network_access is False


def test_unknown_alias_and_negative_tokens_fail_closed() -> None:
    router = ModelRouter()
    with pytest.raises(ValueError, match="Unknown model tier"):
        router.route_request("unknown", 1_000, AuthorityClass.CLASS_0)
    with pytest.raises(ValueError, match="cannot be negative"):
        router.route_request(ModelTier.FAST.value, -1, AuthorityClass.CLASS_0)
