import hashlib
import hmac
from dataclasses import dataclass
from enum import StrEnum


class EvidenceStatus(StrEnum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class Acceptance:
    role: str
    signer_id: str
    evidence_digest: str


class CommissioningGate:
    """Fail-closed gate between verified UAT evidence and production authority."""

    REQUIRED_EVIDENCE = frozenset({
        "authenticated_e2e",
        "tenant_isolation",
        "load",
        "bank_file",
        "failover",
        "disaster_recovery",
        "key_rotation",
    })
    REQUIRED_SIGNERS = frozenset({"GROUP_CEO", "GROUP_CFO"})

    def __init__(self):
        self._evidence = {name: EvidenceStatus.PENDING for name in self.REQUIRED_EVIDENCE}
        self._acceptances: dict[str, Acceptance] = {}
        self._key_version = 1
        self._active_key_ref = "HSM-UAT-v1"

    def record_evidence(self, name: str, status: EvidenceStatus) -> None:
        if name not in self.REQUIRED_EVIDENCE:
            raise ValueError("UNKNOWN_EVIDENCE")
        if not isinstance(status, EvidenceStatus):
            raise TypeError("INVALID_EVIDENCE_STATUS")
        self._evidence[name] = status
        self._acceptances.clear()

    def evidence_digest(self) -> str:
        canonical = "|".join(f"{name}:{self._evidence[name]}" for name in sorted(self._evidence))
        return hashlib.sha256(canonical.encode()).hexdigest()

    def accept(self, *, role: str, signer_id: str, evidence_digest: str) -> None:
        if role not in self.REQUIRED_SIGNERS:
            raise PermissionError("SIGNER_ROLE_NOT_AUTHORIZED")
        if not signer_id.strip():
            raise ValueError("SIGNER_ID_REQUIRED")
        if not hmac.compare_digest(evidence_digest, self.evidence_digest()):
            raise ValueError("STALE_OR_INVALID_EVIDENCE_DIGEST")
        self._acceptances[role] = Acceptance(role, signer_id, evidence_digest)

    def rotate_uat_key(self, *, new_key_ref: str) -> int:
        if not new_key_ref.startswith("HSM-UAT-"):
            raise ValueError("PRODUCTION_KEY_REFERENCE_FORBIDDEN")
        if new_key_ref == self._active_key_ref:
            raise ValueError("KEY_REFERENCE_NOT_CHANGED")
        self._key_version += 1
        self._active_key_ref = new_key_ref
        self._evidence["key_rotation"] = EvidenceStatus.PASSED
        self._acceptances.clear()
        return self._key_version

    def production_authorized(self) -> bool:
        evidence_ready = all(status is EvidenceStatus.PASSED for status in self._evidence.values())
        signers_ready = self.REQUIRED_SIGNERS == self._acceptances.keys()
        distinct_people = len({item.signer_id for item in self._acceptances.values()}) == 2
        digest = self.evidence_digest()
        current_acceptance = all(
            hmac.compare_digest(item.evidence_digest, digest)
            for item in self._acceptances.values()
        )
        return evidence_ready and signers_ready and distinct_people and current_acceptance

    def activation_decision(self, operation: str) -> dict:
        if operation not in {"BML", "MIRA", "PRODUCTION_HSM"}:
            raise ValueError("UNKNOWN_PRODUCTION_OPERATION")
        if not self.production_authorized():
            return {"operation": operation, "decision": "BLOCKED", "reason": "COMMISSIONING_INCOMPLETE"}
        return {"operation": operation, "decision": "ELIGIBLE_FOR_MANUAL_ACTIVATION"}

    @staticmethod
    def validate_bank_file(*, content: bytes, expected_sha256: str, record_count: int) -> dict:
        if not content:
            raise ValueError("EMPTY_BANK_FILE")
        if record_count <= 0:
            raise ValueError("INVALID_RECORD_COUNT")
        actual = hashlib.sha256(content).hexdigest()
        if not hmac.compare_digest(actual, expected_sha256):
            raise ValueError("BANK_FILE_CHECKSUM_MISMATCH")
        return {"sha256": actual, "record_count": record_count, "status": "VALIDATED_NOT_SUBMITTED"}

    @staticmethod
    def reconcile_failover(*, primary_result: str | None, secondary_result: str | None) -> str:
        terminal = {"COMMITTED", "REJECTED"}
        results = {result for result in (primary_result, secondary_result) if result is not None}
        if len(results & terminal) == 1 and len(results) == 1:
            return next(iter(results))
        if not results or len(results) > 1:
            return "UNKNOWN_OUTCOME"
        return "MANUAL_RECONCILIATION"
