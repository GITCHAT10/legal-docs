import pytest
from mnos.modules.ut_aeromarine.kpi_3_30_3 import KPI_3_30_3_Validator
import time

@pytest.mark.asyncio
async def test_kpi_3_30_3_compliance():
    validator = KPI_3_30_3_Validator()
    mid = "M-KPI-1"

    t0 = time.time()
    validator.record_event(mid, "INTAKE", t0)
    validator.record_event(mid, "DECISION", t0 + 2.0) # Within 30s
    validator.record_event(mid, "LAUNCH", t0 + 150.0) # Within 3m (180s)

    report = validator.validate_mission(mid)
    assert report["intake_to_decision"] == 2.0
    assert report["3s_intake_ok"] is True
