import pytest
import time
from mnos.core.aig_aegis.service import aig_aegis

@pytest.fixture(autouse=True)
def aig_aegis_sign_global(monkeypatch):
    def _sign(payload):
        if "nonce" not in payload:
            payload["nonce"] = f"nonce-{time.time()}-{payload.get('device_id')}"
        if "timestamp" not in payload:
            payload["timestamp"] = int(time.time())
        return aig_aegis.sign_session(payload)

    # Inject into modules that need it
    import mnos.final_sovereign_tests
    monkeypatch.setattr("mnos.final_sovereign_tests.aig_aegis_sign", _sign)

    import mnos.tests.rc2_hardening_suite
    monkeypatch.setattr("mnos.tests.rc2_hardening_suite.aig_aegis_sign", _sign)

    import mnos.tests.final_hard_verification
    monkeypatch.setattr("mnos.tests.final_hard_verification.aig_aegis_sign", _sign)

    return _sign
