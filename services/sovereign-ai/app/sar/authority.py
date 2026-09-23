from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, StrEnum


class TrustState(StrEnum):
    TRUSTED = "TRUSTED"
    DEGRADED = "DEGRADED"
    SUSPICIOUS = "SUSPICIOUS"
    REJECTED = "REJECTED"


class AuthorityLevel(IntEnum):
    A0 = 0
    A1 = 1
    A2 = 2


@dataclass
class DynamicAuthority:
    agent_id: str
    authority: AuthorityLevel = AuthorityLevel.A2
    trust: TrustState = TrustState.TRUSTED
    quarantined_domains: set[str] = field(default_factory=set)
    restoration_required: bool = False

    def apply_trust(self, trust: TrustState) -> AuthorityLevel:
        self.trust = trust
        ceiling = {
            TrustState.TRUSTED: AuthorityLevel.A2,
            TrustState.DEGRADED: AuthorityLevel.A1,
            TrustState.SUSPICIOUS: AuthorityLevel.A0,
            TrustState.REJECTED: AuthorityLevel.A0,
        }[trust]
        if ceiling < self.authority:
            self.authority = ceiling
            self.restoration_required = True
        # Trust recovery never raises authority automatically.
        return self.authority

    def x0_quarantine(self, domain: str) -> None:
        self.quarantined_domains.add(domain)
        self.authority = AuthorityLevel.A0
        self.restoration_required = True

    def human_restore(self, authority: AuthorityLevel, *, approved: bool) -> AuthorityLevel:
        if not approved:
            return self.authority
        if self.trust != TrustState.TRUSTED or self.quarantined_domains:
            raise PermissionError("RESTORATION_DENIED: trust/domain containment unresolved")
        self.authority = authority
        self.restoration_required = False
        return self.authority
