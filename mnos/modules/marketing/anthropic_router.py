"""Anthropic model routing policy for the MIG Sovereign Marketing Engine.

This module contains no credentials and performs no direct provider call. It selects an
approved model and execution policy. A credential-vault-backed Anthropic client can consume
the returned ModelDecision at the infrastructure boundary.
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
    notes: str = ""


@dataclass(frozen=True)
class ModelDecision:
    model_id: str
    effort: str
    max_tokens: int
    require_human_approval: bool
    reason: str
    fallback_model_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AnthropicModelPolicy:
    """Fail-closed model selector for agentic marketing and revenue workflows.

    Model identifiers are configurable because provider aliases and availability can change.
    Mythos is never selected by default and requires both an explicit environment flag and
    an approved restricted-access deployment.
    """

    def __init__(self) -> None:
        self.models = {
            "haiku": ModelProfile(
                model_id=os.getenv("ANTHROPIC_HAIKU_MODEL", "claude-haiku-4-5"),
                tier="haiku",
                max_effort="low",
                public_api=True,
                notes="Low-latency classification, routing and short-form transformations.",
            ),
            "sonnet": ModelProfile(
                model_id=os.getenv("ANTHROPIC_SONNET_MODEL", "claude-sonnet-5"),
                tier="sonnet",
                max_effort="high",
                public_api=True,
                notes="Default agentic model for content, research and campaign operations.",
            ),
            "opus": ModelProfile(
                model_id=os.getenv("ANTHROPIC_OPUS_MODEL", "claude-opus-4-8"),
                tier="opus",
                max_effort="high",
                public_api=True,
                notes="Complex planning, repository work and high-value decision support.",
            ),
            "fable": ModelProfile(
                model_id=os.getenv("ANTHROPIC_FABLE_MODEL", "claude-fable-5"),
                tier="fable",
                max_effort="high",
                public_api=True,
                notes="Frontier long-horizon work with provider safety safeguards.",
            ),
            "mythos": ModelProfile(
                model_id=os.getenv("ANTHROPIC_MYTHOS_MODEL", "claude-mythos-5"),
                tier="mythos",
                max_effort="high",
                public_api=False,
                restricted=True,
                notes="Restricted trusted-access model; never enabled for ordinary marketing.",
            ),
        }

    def choose(
        self,
        workload: Workload,
        *,
        risk_level: str = "normal",
        estimated_input_tokens: int = 0,
        contains_personal_data: bool = False,
    ) -> ModelDecision:
        risk = risk_level.lower().strip()
        human_approval = risk in {"high", "critical"} or contains_personal_data

        if workload == Workload.REALTIME:
            return ModelDecision(
                model_id=self.models["haiku"].model_id,
                effort="low",
                max_tokens=2_000,
                require_human_approval=human_approval,
                reason="Low-latency routing, moderation or concise response generation.",
                fallback_model_id=self.models["sonnet"].model_id,
            )

        if workload == Workload.STANDARD:
            return ModelDecision(
                model_id=self.models["sonnet"].model_id,
                effort="medium",
                max_tokens=8_000,
                require_human_approval=human_approval,
                reason="Cost-efficient default for campaign, content and analytics workflows.",
                fallback_model_id=self.models["opus"].model_id,
            )

        if workload == Workload.COMPLEX:
            return ModelDecision(
                model_id=self.models["opus"].model_id,
                effort="high",
                max_tokens=16_000,
                require_human_approval=True,
                reason="Complex multi-step planning, code changes or financially material work.",
                fallback_model_id=self.models["sonnet"].model_id,
            )

        if workload == Workload.FRONTIER:
            return ModelDecision(
                model_id=self.models["fable"].model_id,
                effort="high",
                max_tokens=24_000,
                require_human_approval=True,
                reason="Long-horizon frontier task requiring the strongest generally available tier.",
                fallback_model_id=self.models["opus"].model_id,
            )

        if workload == Workload.SECURITY_REVIEW:
            mythos_enabled = os.getenv("MIG_ENABLE_RESTRICTED_MYTHOS", "false").lower() == "true"
            if mythos_enabled:
                return ModelDecision(
                    model_id=self.models["mythos"].model_id,
                    effort="high",
                    max_tokens=24_000,
                    require_human_approval=True,
                    reason="Restricted defensive-security review under an approved trusted-access program.",
                    fallback_model_id=self.models["fable"].model_id,
                )
            return ModelDecision(
                model_id=self.models["fable"].model_id,
                effort="high",
                max_tokens=16_000,
                require_human_approval=True,
                reason="Mythos access is not enabled; use safeguarded Fable for defensive review.",
                fallback_model_id=self.models["opus"].model_id,
            )

        raise ValueError(f"Unsupported workload: {workload}")

    def catalogue(self) -> Dict[str, Dict[str, Any]]:
        return {name: asdict(profile) for name, profile in self.models.items()}
