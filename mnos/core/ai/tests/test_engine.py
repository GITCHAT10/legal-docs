import pytest
import os
import json
from datetime import datetime, timezone
from pydantic import ValidationError
from mnos.core.ai.models import PrestigeData, BookingData, FinanceData
from mnos.core.ai.engine import AiEngine

@pytest.mark.asyncio
async def test_ai_engine_full_cycle(tmp_path):
    # Ensure any pre-existing decisions.json in CWD is not interfering
    # though engine currently writes to CWD.
    # We will change CWD for this test or mock the save path.
    # For now, let's just remove it if it exists in CWD and then run.
    if os.path.exists("decisions.json"):
        os.remove("decisions.json")

    engine = AiEngine()

    prestige_data = [
        PrestigeData(
            journey_id="J1",
            origin="MLE",
            destination="GAN",
            searches_last_24h=150,
            conversion_rate=0.02,
            competitor_prices={"A": 100.0}
        )
    ]

    booking_data = [
        BookingData(
            route_id="R1",
            total_capacity=100,
            booked_seats=95,
            avg_lead_time_days=10.5,
            cancellation_rate=0.05,
            last_booking_timestamp=datetime.now(timezone.utc)
        )
    ]

    finance_data = [
        FinanceData(
            transaction_id="T1",
            base_amount=1000.0,
            total_amount=1270.0
        )
    ]

    output = await engine.run_optimization_cycle(prestige_data, booking_data, finance_data)

    assert output is not None
    assert os.path.exists("decisions.json")

    # Verify file content is fresh
    with open("decisions.json", "r") as f:
        data = json.load(f)
        assert data["trace_id"] == output.trace_id

def test_booking_data_zero_capacity_rejection():
    with pytest.raises(ValidationError) as excinfo:
        BookingData(
            route_id="R1",
            total_capacity=0,
            booked_seats=0,
            avg_lead_time_days=1.0,
            cancellation_rate=0.0,
            last_booking_timestamp=datetime.now(timezone.utc)
        )
    assert "Input should be greater than 0" in str(excinfo.value)

def test_booking_data_negative_capacity_rejection():
    with pytest.raises(ValidationError) as excinfo:
        BookingData(
            route_id="R1",
            total_capacity=-10,
            booked_seats=0,
            avg_lead_time_days=1.0,
            cancellation_rate=0.0,
            last_booking_timestamp=datetime.now(timezone.utc)
        )
    assert "Input should be greater than 0" in str(excinfo.value)
