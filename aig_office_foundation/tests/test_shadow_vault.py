import pytest
from ..shadow_vault.vault_api import ShadowVault
from ..shadow_audit.ledger import ShadowLedger

@pytest.fixture
def vault():
    ledger = ShadowLedger()
    return ShadowVault(ledger)

def test_vault_upload_download(vault):
    actor = {"identity_id": "u1", "device_id": "d1"}
    data = b"Hello Sovereign Data"
    trace_id = "trace-upload-001"

    file_id = vault.upload_file(actor, "secret.txt", data, trace_id)
    assert file_id is not None

    # Download
    downloaded = vault.download_file(actor, file_id, "trace-download-001")
    assert downloaded == data

    # Audit trail check
    assert len(vault.shadow_ledger.ledger) == 2
    assert vault.shadow_ledger.ledger[0]["data"]["event_type"] == "vault.file.uploaded"
    assert vault.shadow_ledger.ledger[1]["data"]["event_type"] == "vault.file.downloaded"

def test_vault_access_control(vault):
    owner = {"identity_id": "owner", "device_id": "d1"}
    attacker = {"identity_id": "attacker", "device_id": "d2"}
    data = b"Owner Secrets"

    file_id = vault.upload_file(owner, "private.txt", data, "t1")

    with pytest.raises(PermissionError, match="Access denied"):
        vault.download_file(attacker, file_id, "t2")

def test_vault_sharing(vault):
    owner = {"identity_id": "owner", "device_id": "d1"}
    friend = {"identity_id": "friend", "device_id": "d2"}
    data = b"Shared Info"

    file_id = vault.upload_file(owner, "shared.txt", data, "t1")

    # Before sharing
    with pytest.raises(PermissionError):
        vault.download_file(friend, file_id, "t2")

    # Share
    vault.share_file(owner, file_id, friend["identity_id"], "t3")

    # After sharing
    downloaded = vault.download_file(friend, file_id, "t4")
    assert downloaded == data
