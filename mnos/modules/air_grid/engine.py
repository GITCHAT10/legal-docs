import uuid
import hashlib
import json
from datetime import datetime, time, timedelta, UTC
from typing import Dict, List, Any, Optional
from decimal import Decimal

class AirGridEngine:
    """
    A.I.D.A.S. Air Traffic Command Engine: Orchestrates flight intake to island dispatch.
    """
    def __init__(self, core):
        self.core = core
        self.corridors = {
            "INDIA_SOUTH": {"preferred_transfer": "speedboat", "multiplier": Decimal("1.0")},
            "GCC_DXB": {"preferred_transfer": "seaplane", "multiplier": Decimal("1.15")},
            "ASEAN_KUL": {"preferred_transfer": "speedboat", "multiplier": Decimal("1.0")}
        }
        self.arrival_windows = [
            {"start": time(9, 0), "end": time(11, 0), "id": "W-MORNING-1"},
            {"start": time(14, 0), "end": time(16, 0), "id": "W-AFTERNOON-1"},
            {"start": time(20, 0), "end": time(23, 59), "id": "W-NIGHT-1"}
        ]
        self.flights = {} # flight_id -> data

    def ingest_flight_update(self, actor_ctx: dict, flight_data: dict):
        """MANDATORY ENTRYPOINT for flight tracking."""
        return self.core.execute_commerce_action(
            "air_grid.flight.ingest",
            actor_ctx,
            self._internal_ingest,
            flight_data
        )

    def _internal_ingest(self, data):
        flight_id = data.get("flight_id")
        # 1. Normalize
        scheduled = datetime.fromisoformat(data.get("scheduled_arrival"))
        estimated = datetime.fromisoformat(data.get("estimated_arrival", data.get("scheduled_arrival")))

        delay_min = (estimated - scheduled).total_seconds() / 60

        # 2. Match Window
        window = self._match_window(estimated.time())

        flight = {
            "flight_id": flight_id,
            "corridor": data.get("corridor"),
            "status": data.get("status", "scheduled"),
            "scheduled": scheduled.isoformat(),
            "estimated": estimated.isoformat(),
            "delay_minutes": delay_min,
            "pax_count": data.get("pax_count", 0),
            "window": window,
            "last_updated": datetime.now(UTC).isoformat()
        }

        self.flights[flight_id] = flight
        self.core.events.publish("air_grid.flight_updated", flight)
        return flight

    def _match_window(self, arrival_time: time) -> str:
        for w in self.arrival_windows:
            if w["start"] <= arrival_time <= w["end"]:
                return w["id"]
        return "W-DEFAULT"

    def assign_transfer(self, actor_ctx: dict, flight_id: str):
        return self.core.execute_commerce_action(
            "air_grid.transfer.assign",
            actor_ctx,
            self._internal_assign,
            flight_id
        )

    def _internal_assign(self, flight_id: str):
        flight = self.flights.get(flight_id)
        if not flight: raise ValueError("Flight not found")

        corridor = self.corridors.get(flight["corridor"], self.corridors["INDIA_SOUTH"])

        # 1. Determine Mode
        mode = corridor["preferred_transfer"]

        # 2. Revenue-Pulse: Dynamic Pricing
        # If delay < 30min or high urgency, apply multiplier
        multiplier = corridor["multiplier"]
        if flight["delay_minutes"] > 0 and flight["delay_minutes"] < 30:
            multiplier += Decimal("0.05") # Urgency premium

        assignment = {
            "flight_id": flight_id,
            "transfer_mode": mode,
            "multiplier": float(multiplier),
            "status": "ASSIGNED",
            "assigned_at": datetime.now(UTC).isoformat()
        }

        # 3. Audit via SHADOW (Implicitly handled by execute_commerce_action)
        self.core.events.publish("air_grid.transfer_assigned", assignment)
        return assignment

    def confirm_landing(self, actor_ctx: dict, flight_id: str):
        return self.core.execute_commerce_action(
            "air_grid.flight.landed",
            actor_ctx,
            self._internal_land,
            flight_id
        )

    def _internal_land(self, flight_id: str):
        flight = self.flights.get(flight_id)
        if not flight: raise ValueError("Flight not found")

        flight["status"] = "landed"
        flight["actual_arrival"] = datetime.now(UTC).isoformat()

        self.core.events.publish("air_grid.flight_landed", flight)
        return flight
