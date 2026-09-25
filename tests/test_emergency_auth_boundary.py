import pytest
from fastapi import HTTPException

from main import get_actor_ctx


def test_predictable_direct_signature_rejected_outside_local_simulation(monkeypatch):
    monkeypatch.delenv("MNOS_ENV", raising=False)
    monkeypatch.delenv("MNOS_ENABLE_SIMULATED_IDENTITY", raising=False)
    with pytest.raises(HTTPException) as caught:
        get_actor_ctx(
            x_aegis_session=None,
            x_aegis_identity="untrusted",
            x_aegis_device="device",
            x_aegis_signature="VALID_SIG_FOR_untrusted",
        )
    assert caught.value.status_code == 403
    assert caught.value.detail == "DIRECT_AEGIS_AUTH_DISABLED"
