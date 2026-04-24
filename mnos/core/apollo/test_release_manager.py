import pytest
from mnos.core.apollo.release_manager import ReleaseManager, DeploymentStatus

def test_apollo_promotion_requires_guard_report():
    rm = ReleaseManager({})
    ctx = {
        "user_id": "CEO",
        "session_id": "S1",
        "device_id": "nexus-001",
        "issued_at": 1700000000,
        "nonce": "N1",
        "signature": "SIG"
    }
    # If GUARD_PROOF_REPORT.json is deleted, it should fail
    import os
    if os.path.exists("GUARD_PROOF_REPORT.json"):
        with pytest.raises(RuntimeError, match="Promotion failed"):
            # Move it temporarily
            os.rename("GUARD_PROOF_REPORT.json", "TEMP_REPORT.json")
            try:
                rm.promote("art-1", DeploymentStatus.PROD, ctx)
            finally:
                os.rename("TEMP_REPORT.json", "GUARD_PROOF_REPORT.json")
