import pytest

from app.model_router import CapabilityTier, ModelRoute, Workload, route_for, validate_route


def test_finance_requires_human_approval() -> None:
    route = route_for(Workload.FINANCE)
    assert route.requires_human_approval is True
    assert route.production_write_access is False


def test_cybersecurity_has_no_default_network_access() -> None:
    route = route_for(Workload.CYBERSECURITY)
    assert route.tier == CapabilityTier.ULTRA_GUARDED
    assert route.network_access is False


def test_rejects_unrestricted_route() -> None:
    route = ModelRoute(
        provider="anthropic",
        model_alias="unsafe",
        tier=CapabilityTier.ULTRA_GUARDED,
        max_reasoning_budget=32_000,
        requires_human_approval=True,
        network_access=True,
    )
    with pytest.raises(ValueError):
        validate_route(route)


def test_high_capability_route_cannot_bypass_approval() -> None:
    route = ModelRoute(
        provider="anthropic",
        model_alias="unsafe",
        tier=CapabilityTier.DEEP_REASONING,
        max_reasoning_budget=16_000,
        requires_human_approval=False,
    )
    with pytest.raises(ValueError):
        validate_route(route)
