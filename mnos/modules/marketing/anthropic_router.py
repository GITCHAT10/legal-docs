"""Anthropic model routing policy for the MIG Sovereign Marketing Engine.

The policy performs no provider call and contains no credentials. It selects a model,
containment policy, approval requirement and telemetry classification for an infrastructure
adapter that obtains credentials from the hardware-backed secret vault.
"""

from dataclasses import asdict, dataclass
from enum import Enum
import os
from typing import Any, Dict, Optional


class Workload(str, Enum):
    REALTIME = "realtime"
    STANDARD = "standard"
    COMPLEX = "complex"
    FRONTIER = "frontier"
    SECURITY_REVIEW = "security_review"


@dataclass(frozen=True)
class ModelProfile:
    model_id: str
    tier: str
    max_effort: str
    public_api: bool
    restricted: bool = False
    context_limit: int = 0
    notes: str = ""


@dataclass(frozen=True)
class ModelDecision:
    model_id: str
    effort: str
    max_tokens: int
    require_human_approval: bool
    containment: str
    telemetry_class: str
    reason: str
    fallback_model_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AnthropicModelPolicy:
    """Fail-closed model selector for agentic marketing and revenue workflows.

    Provider identifiers use Claude Platform API IDs/aliases. They remain environment
    configurable so deployment can pin snapshots or migrate without changing application code.
    Mythos is never selected by default and requires explicit Project Glasswing access.
    """

    def __init__(self) -> None:
        self.models = {
            "haiku": ModelProfile(
                model_id=os.getenv("ANTHROPIC_HAIKU_MODEL", "claude-haiku-4-5"),
                tier="haiku",
                max_effort="low",
                public_api=True,
                context_limit=200_000,
                notes="Low-latency classification, routing and short-form transformations.",
            ),
            "sonnet": ModelProfile(
                model_id=os.getenv("ANTHROPIC_SONNET_MODEL", "claude-sonnet-5"),
                tier="sonnet",
                max_effort="high",
                public_api=True,
                context_limit=1_000_000,
                notes="Default agentic model for content, research and campaign operations.",
            ),
            "opus": ModelProfile(
                model_id=os.getenv("ANTHROPIC_OPUS_MODEL", "claude-opus-4-8"),
                tier="opus",
                max_effort="high",
                public_api=True,
                context_limit=1_000_000,
                notes="Complex planning, repository work and financially material oversight.",
            ),
            "fable": ModelProfile(
                model_id=os.getenv("ANTHROPIC_FABLE_MODEL", "claude-fable-5"),
                tier="fable",
                max_effort="high",
                public_api=True,
                context_limit=1_000_000,
                notes="Frontier long-horizon work with provider safeguards.",
            ),
            "mythos": ModelProfile(
                model_id=os.getenv("ANTHROPIC_MYTHOS_MODEL", "claude-mythos-5"),
                tier="mythos",
                max_effort="high",
                public_api=False,
                restricted=True,
                context_limit=1_000_000,
                notes="Project Glasswing restricted defensive-security model.",
            ),
        }

    def choose(
        self,
        workload: Workload,
        *,
        risk_level: str = "normal",
        estimated_input_tokens: int = 0,
        contains_personal_data: bool = False,
        class_3_action: bool = False,
        security_override: Optional[str] = None,
    ) -> ModelDecision:
        if estimated_input_tokens < 0:
            raise ValueError("estimated_input_tokens must be non-negative")

        risk = risk_level.lower().strip()
        elevated = risk in {"high", "critical"} or contains_personal_data or class_3_action

        # PII and Class-3 financial/governance work must use the controlled complex tier.
        if elevated and workload not in {Workload.SECURITY_REVIEW, Workload.FRONTIER}:
            return self._decision(
                "opus", "high", 16_000, True, "high_risk",
                "High-risk, personal-data or Class-3 action requires controlled Opus review.",
                fallback="sonnet",
            )

        if workload == Workload.REALTIME:
            # Keep Haiku traffic bounded even though its documented context is larger.
            if estimated_input_tokens > 50_000:
                return self._decision(
                    "sonnet", "medium", 8_000, elevated, "standard",
                    "Realtime payload exceeds the 50k MIG fast-path limit; promoted to Sonnet.",
                    fallback="opus",
                )
            return self._decision(
                "haiku", "low", 2_000, elevated, "fast_path",
                "Low-latency routing, telemetry classification or concise generation.",
                fallback="sonnet",
            )

        if workload == Workload.STANDARD:
            return self._decision(
                "sonnet", "medium", 8_000, elevated, "standard",
                "Default campaign, optimization, content and analytics workflow.",
                fallback="opus",
            )

        if workload == Workload.COMPLEX:
            return self._decision(
                "opus", "high", 16_000, True, "high_risk",
                "Complex repository, ledger-validation or financially material workflow.",
                fallback="sonnet",
            )

        if workload == Workload.FRONTIER:
            return self._decision(
                "fable", "high", 24_000, True, "frontier_isolated",
                "Long-horizon frontier workflow; output is proposal-only pending approval.",
                fallback="opus",
            )

        if workload == Workload.SECURITY_REVIEW:
            access_enabled = os.getenv("MIG_PROJECT_GLASSWING_ACCESS", "false").lower() == "true"
            enclave_enabled = os.getenv("MIG_GLASSWING_LOCAL_ENCLAVE", "false").lower() == "true"
            if security_override == "MYTHOS_REQUEST":
                if not (access_enabled and enclave_enabled):
                    raise PermissionError(
                        "Mythos is locked: approved Project Glasswing access and local enclave are required."
                    )
                return self._decision(
                    "mythos", "high", 24_000, True, "glasswing_enclave",
                    "Restricted defensive-security review inside the isolated Glasswing enclave.",
                    fallback=None,
                )
            return self._decision(
                "fable", "high", 16_000, True, "defensive_isolated",
                "Restricted model was not explicitly requested; use safeguarded Fable review.",
                fallback="opus",
            )

        raise ValueError(f"Unsupported workload: {workload}")

    def _decision(
        self,
        model: str,
        effort: str,
        max_tokens: int,
        approval: bool,
        telemetry_class: str,
        reason: str,
        *,
        fallback: Optional[str],
    ) -> ModelDecision:
        profile = self.models[model]
        return ModelDecision(
            model_id=profile.model_id,
            effort=effort,
            max_tokens=max_tokens,
            require_human_approval=approval,
            containment="proposal_only" if approval else "direct_execution",
            telemetry_class=telemetry_class,
            reason=reason,
            fallback_model_id=self.models[fallback].model_id if fallback else None,
        )

    def catalogue(self) -> Dict[str, Dict[str, Any]]:
        return {name: asdict(profile) for name, profile in self.models.items()}
