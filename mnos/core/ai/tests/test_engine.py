import pytest
import os
from datetime import datetime, timezone
from mnos.core.ai.models import PrestigeData, BookingData, FinanceData
from mnos.core.ai.engine import AiEngine

@pytest.mark.asyncio
async def test_ai_engine_full_cycle():
    engine = AiEngine()

    prestige_data = [
        PrestigeData(
            journey_id="J1",
            origin="MLE",
            destination="GAN",
            searches_last_24h=150,
            conversion_rate=0.02,
            competitor_prices={"A": 100.0}
        ),
        PrestigeData(
            journey_id="J2",
            origin="MLE",
            destination="VAM",
            searches_last_24h=600,
            conversion_rate=0.1,
            competitor_prices={"A": 120.0}
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
        ),
        BookingData(
            route_id="R2",
            total_capacity=50,
            booked_seats=10,
            avg_lead_time_days=2.0,
            cancellation_rate=0.1,
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
    assert len(output.decisions) > 0
    assert os.path.exists("decisions.json")

    # Check for specific decisions based on input
    modules_in_decisions = [d.module for d in output.decisions]
    assert "routing_optimizer" in modules_in_decisions
    assert "demand_predictor" in modules_in_decisions
    assert "revenue_optimizer" in modules_in_decisions

    # Verify content of decisions.json
    with open("decisions.json", "r") as f:
        data = f.read()
        assert "MLE-GAN" in data
        assert "UPGRADE_VESSEL" in data
        assert "PREDICT_SURGE" in data
        assert "APPLY_DISCOUNT" in data
