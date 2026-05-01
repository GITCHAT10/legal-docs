import pytest
from mnos.modules.ut_aeromarine.mission_schema import UTAMMission, MissionStatus

@pytest.mark.asyncio
async def test_fce_billing_blocked_without_shadow_seal(utam_stack):
    _, _, _, _, billing = utam_stack
    mission = UTAMMission(mission_id="M-1", commercial_billable=True, status=MissionStatus.LAUNCHED)

    with pytest.raises(RuntimeError) as exc:
        billing.release_billing(mission)
    assert "not SHADOW_SEALED" in str(exc.value)
