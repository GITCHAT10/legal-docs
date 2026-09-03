import hashlib

import pytest

from mnos.modules.commissioning import CommissioningGate, EvidenceStatus


def test_production_is_blocked_until_all_evidence_and_dual_acceptance():
    gate = CommissioningGate()
    assert gate.activation_decision("BML")["decision"] == "BLOCKED"
    for name in gate.REQUIRED_EVIDENCE:
        gate.record_evidence(name, EvidenceStatus.PASSED)
    digest = gate.evidence_digest()
    gate.accept(role="GROUP_CEO", signer_id="CEO-1", evidence_digest=digest)
    assert gate.activation_decision("MIRA")["decision"] == "BLOCKED"
    gate.accept(role="GROUP_CFO", signer_id="CFO-1", evidence_digest=digest)
    assert gate.activation_decision("PRODUCTION_HSM")["decision"] == "ELIGIBLE_FOR_MANUAL_ACTIVATION"


def test_same_person_cannot_satisfy_dual_signatory_gate():
    gate = CommissioningGate()
    for name in gate.REQUIRED_EVIDENCE:
        gate.record_evidence(name, EvidenceStatus.PASSED)
    digest = gate.evidence_digest()
    gate.accept(role="GROUP_CEO", signer_id="PERSON-1", evidence_digest=digest)
    gate.accept(role="GROUP_CFO", signer_id="PERSON-1", evidence_digest=digest)
    assert gate.production_authorized() is False


def test_new_evidence_invalidates_prior_acceptance():
    gate = CommissioningGate()
    digest = gate.evidence_digest()
    gate.accept(role="GROUP_CEO", signer_id="CEO-1", evidence_digest=digest)
    gate.record_evidence("load", EvidenceStatus.FAILED)
    with pytest.raises(ValueError, match="STALE_OR_INVALID"):
        gate.accept(role="GROUP_CFO", signer_id="CFO-1", evidence_digest=digest)


def test_bank_file_checksum_is_validated_without_submission():
    content = b"MIG-UAT-BANK-FILE\nTX-1,1000.00,MVR\n"
    digest = hashlib.sha256(content).hexdigest()
    result = CommissioningGate.validate_bank_file(content=content, expected_sha256=digest, record_count=1)
    assert result["status"] == "VALIDATED_NOT_SUBMITTED"
    with pytest.raises(ValueError, match="CHECKSUM_MISMATCH"):
        CommissioningGate.validate_bank_file(content=content, expected_sha256="0" * 64, record_count=1)


def test_failover_never_guesses_conflicting_or_missing_outcome():
    assert CommissioningGate.reconcile_failover(primary_result="COMMITTED", secondary_result=None) == "COMMITTED"
    assert CommissioningGate.reconcile_failover(primary_result=None, secondary_result=None) == "UNKNOWN_OUTCOME"
    assert CommissioningGate.reconcile_failover(primary_result="COMMITTED", secondary_result="REJECTED") == "UNKNOWN_OUTCOME"


def test_only_uat_key_references_can_rotate_in_preproduction():
    gate = CommissioningGate()
    assert gate.rotate_uat_key(new_key_ref="HSM-UAT-v2") == 2
    with pytest.raises(ValueError, match="PRODUCTION_KEY_REFERENCE_FORBIDDEN"):
        gate.rotate_uat_key(new_key_ref="HSM-PROD-v2")
