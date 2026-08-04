"""Operational security defaults for MIG Marketing Intel-Mesh staging.

No JWT signing implementation lives here. This module defines centrally testable policy
limits consumed by the identity gateway and telemetry adapters.
"""

from dataclasses import asdict, dataclass
import os
from typing import Any, Dict


@dataclass(frozen=True)
class TelemetryPolicy:
    backend: str
    metrics_endpoint: str
    audit_sink: str
    export_prompt_content: bool
    export_personal_data: bool
    retention_days: int


@dataclass(frozen=True)
class TokenPolicy:
    access_ttl_seconds: int
    privileged_ttl_seconds: int
    approval_ttl_seconds: int
    refresh_ttl_seconds: int
    clock_skew_seconds: int


class MarketingOperationalSecurity:
    """Fail-closed staging defaults for observability and ephemeral credentials."""

    MIN_ACCESS_TTL = 300
    MAX_ACCESS_TTL = 1_800
    MAX_PRIVILEGED_TTL = 600
    MAX_APPROVAL_TTL = 300
    MAX_REFRESH_TTL = 86_400

    def __init__(self) -> None:
        self.telemetry = TelemetryPolicy(
            backend=os.getenv("MIG_MARKETING_TELEMETRY_BACKEND", "prometheus_local"),
            metrics_endpoint=os.getenv("MIG_MARKETING_METRICS_ENDPOINT", "/internal/metrics"),
            audit_sink=os.getenv("MIG_MARKETING_AUDIT_SINK", "shadow_ledger_syslog"),
            export_prompt_content=False,
            export_personal_data=False,
            retention_days=int(os.getenv("MIG_MARKETING_TELEMETRY_RETENTION_DAYS", "30")),
        )
        self.tokens = TokenPolicy(
            access_ttl_seconds=int(os.getenv("MIG_MARKETING_JWT_ACCESS_TTL", "900")),
            privileged_ttl_seconds=int(os.getenv("MIG_MARKETING_JWT_PRIVILEGED_TTL", "300")),
            approval_ttl_seconds=int(os.getenv("MIG_MARKETING_JWT_APPROVAL_TTL", "180")),
            refresh_ttl_seconds=int(os.getenv("MIG_MARKETING_JWT_REFRESH_TTL", "43200")),
            clock_skew_seconds=int(os.getenv("MIG_MARKETING_JWT_CLOCK_SKEW", "30")),
        )
        self.validate()

    def validate(self) -> None:
        t = self.tokens
        if not self.MIN_ACCESS_TTL <= t.access_ttl_seconds <= self.MAX_ACCESS_TTL:
            raise ValueError("Access JWT TTL must be between 5 and 30 minutes")
        if not 60 <= t.privileged_ttl_seconds <= self.MAX_PRIVILEGED_TTL:
            raise ValueError("Privileged JWT TTL must be between 1 and 10 minutes")
        if not 60 <= t.approval_ttl_seconds <= self.MAX_APPROVAL_TTL:
            raise ValueError("Approval JWT TTL must be between 1 and 5 minutes")
        if not 3_600 <= t.refresh_ttl_seconds <= self.MAX_REFRESH_TTL:
            raise ValueError("Refresh JWT TTL must be between 1 and 24 hours")
        if not 0 <= t.clock_skew_seconds <= 60:
            raise ValueError("JWT clock skew must be between 0 and 60 seconds")
        if not 1 <= self.telemetry.retention_days <= 90:
            raise ValueError("Telemetry retention must be between 1 and 90 days")

    def public_config(self) -> Dict[str, Any]:
        return {
            "telemetry": asdict(self.telemetry),
            "tokens": asdict(self.tokens),
        }
