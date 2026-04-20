import pytest
import os
import json
import time
from datetime import datetime, timezone
from pydantic import ValidationError
from mnos.core.ai.models import PrestigeData, BookingData, FinanceData
from mnos.core.ai.engine import AiEngine

@pytest.mark.asyncio
async def test_ai_engine_full_cycle():
    # TEST ISOLATION FIX
    if os.path.exists("decisions.json"):
        os.remove("decisions.json")

    assert not os.path.exists("decisions.json")
    start_time = time.time()

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

    # ASSERTION: file created during test runtime only
    assert os.path.exists("decisions.json")
    file_mtime = os.path.getmtime("decisions.json")
    # Using a small epsilon or ensuring start_time is captured before any potential rounding
    assert file_mtime >= (start_time - 0.1)

    # Verify content
    with open("decisions.json", "r") as f:
        data = json.load(f)
        assert data["trace_id"] == output.trace_id
        assert data["advisory_only"] is True
        assert "confidence_score" in data
        assert "policy_score" in data

def test_booking_data_validation():
    # Enforce strict validation: total_capacity must be > 0
    with pytest.raises(ValidationError):
        BookingData(
            route_id="R1",
            total_capacity=0,
            booked_seats=0,
            avg_lead_time_days=1.0,
            cancellation_rate=0.0,
            last_booking_timestamp=datetime.now(timezone.utc)
        )

@pytest.mark.asyncio
async def test_ai_engine_fail_closed():
    engine = AiEngine()
    # Trigger a crash by passing None where lists are expected
    output = await engine.run_optimization_cycle(None, [], [])

    assert output.decisions == []
    assert output.advisory_only is True
    assert "error" in output.metadata
