from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CapabilityTier(StrEnum):
    FAST = "FAST"
    BALANCED = "BALANCED"
    DEEP_REASONING = "DEEP_REASONING"
    ULTRA_GUARDED = "ULTRA_GUARDED"


class Workload(StrEnum):
    CLASSIFICATION = "CLASSIFICATION"
    CUSTOMER_SERVICE = "CUSTOMER_SERVICE"
    OPERATIONS = "OPERATIONS"
    FINANCE = "FINANCE"
    LEGAL = "LEGAL"
    SOFTWARE_ENGINEERING = "SOFTWARE_ENGINEERING"
    CYBERSECURITY = "CYBERSECURITY"
    EXECUTIVE_STRATEGY = "EXECUTIVE_STRATEGY"


@dataclass(frozen=True)
class ModelRoute:
    provider: str
    model_alias: str
    tier: CapabilityTier
    max_reasoning_budget: int
    requires_human_approval: bool
    network_access: bool = False
    production_write_access: bool = False


# Aliases are resolved by deployment configuration. They are not assumed to be
# valid provider API identifiers until verified against the connected account.
ROUTES: dict[Workload, ModelRoute] = {
    Workload.CLASSIFICATION: ModelRoute("anthropic", "claude-fast", CapabilityTier.FAST, 1_000, False),
    Workload.CUSTOMER_SERVICE: ModelRoute("anthropic", "claude-balanced", CapabilityTier.BALANCED, 4_000, False),
    Workload.OPERATIONS: ModelRoute("anthropic", "claude-balanced", CapabilityTier.BALANCED, 8_000, False),
    Workload.FINANCE: ModelRoute("anthropic", "claude-deep", CapabilityTier.DEEP_REASONING, 16_000, True),
    Workload.LEGAL: ModelRoute("anthropic", "claude-deep", CapabilityTier.DEEP_REASONING, 20_000, True),
    Workload.SOFTWARE_ENGINEERING: ModelRoute("anthropic", "claude-deep", CapabilityTier.DEEP_REASONING, 24_000, True),
    Workload.CYBERSECURITY: ModelRoute("anthropic", "claude-ultra-guarded", CapabilityTier.ULTRA_GUARDED, 24_000, True),
    Workload.EXECUTIVE_STRATEGY: ModelRoute("anthropic", "claude-ultra-guarded", CapabilityTier.ULTRA_GUARDED, 32_000, True),
}


def route_for(workload: Workload) -> ModelRoute:
    return ROUTES[workload]


def validate_route(route: ModelRoute) -> None:
    if route.network_access or route.production_write_access:
        raise ValueError("Model routes cannot directly receive unrestricted network or production write access")
    if route.tier in {CapabilityTier.DEEP_REASONING, CapabilityTier.ULTRA_GUARDED} and not route.requires_human_approval:
        raise ValueError("High-capability routes require human approval")
