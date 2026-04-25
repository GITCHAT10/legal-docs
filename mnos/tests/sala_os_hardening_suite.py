import pytest
from mnos.interfaces.sala_os.security.guard import sala_guard
from mnos.interfaces.sala_os.deployment import ui_deployment
from mnos.core.security.aegis import aegis, SecurityException

def test_cockpit_unauthorized_request_rejected():
    """Verify UI access fails without signed session."""
    ctx = {"device_id": "nexus-001"} # No signature
    with pytest.raises(SecurityException):
        ui_deployment.serve_interface(ctx)

def test_cockpit_forged_session_rejected():
    """Verify UI access fails with forged signature."""
    ctx = {"device_id": "nexus-001", "signature": "FORGED"}
    with pytest.raises(SecurityException):
        ui_deployment.serve_interface(ctx)

def test_direct_privileged_api_access_blocked():
    """Verify core APIs require sovereign context (Execution Guard)."""
    from mnos.modules.shadow.service import shadow
    # Direct write outside guard should fail
    with pytest.raises(RuntimeError, match="SOVEREIGN VIOLATION"):
        shadow.commit("rogue_write", {"data": "attack"})
