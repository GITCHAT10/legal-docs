"""
MIG Sovereign AI Grid v2 - Model Router
Path: services/sovereign-ai/app/model_router.py
Status: Locked implementation contract (PR #52 / PR #7)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from typing import Mapping


class ModelTier(StrEnum):
    FAST = "claude-fast"
    BALANCED = "claude-balanced"
    DEEP_REASONING = "claude-deep"
    ULTRA_GUARDED = "claude-ultra-guarded"


class AuthorityClass(IntEnum):
    CLASS_0 = 0  # Read-only / observational
    CLASS_1 = 1  # Standard operations
    CLASS_2 = 2  # Advanced operational logic
    CLASS_3 = 3  # Privileged or high-value actions
    CLASS_4 = 4  # Infrastructure / root adjustments


class SecurityError(RuntimeError):
    """Raised when an execution vector violates sovereign containment rules."""


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    resolved_model_id: str
    tier: ModelTier
    requires_human_approval: bool
    containment_level: str
    telemetry_classification: str
    permits_network_access: bool = False
    permits_production_write: bool = False


class ModelRouter:
    """Fail-closed model router for the MIG Sovereign AI control plane."""

    MAX_FAST_PATH_TOKENS = 50_000

    def __init__(self, alias_matrix: Mapping[ModelTier, str] | None = None) -> None:
        # Provider identifiers remain deployment-configurable so a renamed,
        # withdrawn, region-blocked or unavailable model fails closed rather
        # than silently routing to an unintended model.
        defaults: dict[ModelTier, str] = {
            ModelTier.FAST: os.getenv("ANTHROPIC_MODEL_FAST", "claude-haiku-4-5"),
            ModelTier.BALANCED: os.getenv("ANTHROPIC_MODEL_BALANCED", "claude-sonnet-5"),
            ModelTier.DEEP_REASONING: os.getenv("ANTHROPIC_MODEL_DEEP", "claude-opus-4-8"),
            ModelTier.ULTRA_GUARDED: os.getenv("ANTHROPIC_MODEL_GUARDED", "claude-fable-5"),
        }
        self._alias_matrix = dict(alias_matrix or defaults)
        self._glasswing_enabled = self._env_true("PROJECT_GLASSWING_ACCESS")
        self._local_enclave_declared = bool(os.getenv("MALDIVES_LOCAL_ENCLAVE", "").strip())
        self._pii_external_processing_allowed = self._env_true("PII_EXTERNAL_PROCESSING_ALLOWED")

    @staticmethod
    def _env_true(name: str) -> bool:
        return os.getenv(name, "FALSE").strip().upper() == "TRUE"

    def route_request(
        self,
        tier_alias: str,
        estimated_input_tokens: int,
        authority: AuthorityClass,
        payload_contains_pii: bool = False,
    ) -> RoutingDecision:
        """Validate and lock routing containment for an agent execution."""
        if estimated_input_tokens < 0:
            raise ValueError("CRITICAL_FAIL_CLOSED: Token estimate cannot be negative")
        if not isinstance(authority, AuthorityClass):
            raise ValueError("CRITICAL_FAIL_CLOSED: Invalid authority class")

        try:
            target_tier = ModelTier(tier_alias)
        except ValueError as exc:
            raise ValueError(
                f"CRITICAL_FAIL_CLOSED: Unknown model tier alias: {tier_alias!r}"
            ) from exc

        # PII may never be sent to an external provider merely because a more
        # capable model was selected. The deployment must explicitly authorize
        # external PII processing after legal, residency and retention review.
        if payload_contains_pii and not self._pii_external_processing_allowed:
            raise SecurityError(
                "CRITICAL_FAIL_CLOSED: External PII processing is not authorized"
            )

        if payload_contains_pii or authority >= AuthorityClass.CLASS_3:
            target_tier = ModelTier.DEEP_REASONING

        if (
            target_tier is ModelTier.FAST
            and estimated_input_tokens > self.MAX_FAST_PATH_TOKENS
        ):
            target_tier = ModelTier.BALANCED

        resolved_model = self._alias_matrix.get(target_tier, "").strip()
        if not resolved_model:
            raise RuntimeError(
                f"CRITICAL_FAIL_CLOSED: Alias path {target_tier.value!r} failed to resolve"
            )

        if target_tier is ModelTier.ULTRA_GUARDED:
            # Mythos is restricted to approved Glasswing partners and is never
            # enabled by a model-name request alone.
            if not (self._glasswing_enabled and self._local_enclave_declared):
                raise SecurityError(
                    "CRITICAL_FAIL_CLOSED: Ultra-guarded access denied; "
                    "Glasswing and local enclave controls are unverified"
                )
            resolved_model = os.getenv("ANTHROPIC_MODEL_MYTHOS", "claude-mythos-5").strip()
            if not resolved_model:
                raise SecurityError("CRITICAL_FAIL_CLOSED: Mythos model is unresolved")

        requires_hitl = authority >= AuthorityClass.CLASS_3 or payload_contains_pii
        containment = (
            "SANDBOXED_NO_NET"
            if target_tier is ModelTier.ULTRA_GUARDED
            else "STANDARD_CONTAINMENT"
        )
        telemetry = (
            "RESTRICTED_METRICS_ONLY" if payload_contains_pii else "FULL_PROMETHEUS"
        )

        return RoutingDecision(
            resolved_model_id=resolved_model,
            tier=target_tier,
            requires_human_approval=requires_hitl,
            containment_level=containment,
            telemetry_classification=telemetry,
            permits_network_access=False,
            permits_production_write=False,
        )
