import uuid
from fastapi import FastAPI, HTTPException, Depends
from mnos.modules.telemetry.schemas import (
    HandshakeRequest, HandshakeResponse, TelemetryPacket, ComfortIndex, FlightState
)
from mnos.modules.telemetry.service import StabilityArbiter
from mnos.shared.sdk.mnos_client import MnosClient
from datetime import datetime, timezone

app = FastAPI(title="SS Telemetry Service")
mnos_client = MnosClient()
arbiter = StabilityArbiter()

# In-memory session storage (use Redis in production)
sessions = {}

@app.post("/handshake", response_model=HandshakeResponse)
async def handshake(request: HandshakeRequest):
    session_token = str(uuid.uuid4())
    sessions[session_token] = request.vessel_id

    return HandshakeResponse(
        status="CONNECTED",
        session_token=session_token,
        heartbeat_interval_seconds=5
    )

@app.post("/heartbeat")
async def heartbeat(session_token: str):
    if session_token not in sessions:
        raise HTTPException(status_code=401, detail="Invalid session token")
    return {"status": "OK", "timestamp": datetime.now(timezone.utc)}

@app.post("/telemetry")
async def ingest_telemetry(packet: TelemetryPacket):
    if packet.session_token not in sessions:
        raise HTTPException(status_code=401, detail="Invalid session token")

    # Process Comfort Index
    comfort = arbiter.calculate_comfort_index(packet)

    # Emit foiling state changes
    # (Implementation of state tracking would go here, for now just emit the event)
    if packet.flight_state == FlightState.FOILING:
        await mnos_client.emit_event(
            "ss.vessel.flight_active",
            {
                "vessel_id": packet.vessel_id,
                "flying_height": packet.flying_height,
                "efficiency": comfort.flight_efficiency
            }
        )

    # Check for High Roll/Discomfort Zone (4.0 threshold)
    if comfort.score >= 4.0:
        await mnos_client.emit_event(
            "ss.vessel.comfort_alert",
            {
                "vessel_id": packet.vessel_id,
                "score": comfort.score,
                "status": comfort.status,
                "flight_state": packet.flight_state,
                "recommendation": comfort.recommendation,
                "location": {"lat": packet.gnss.latitude, "lon": packet.gnss.longitude}
            }
        )

    # Check for G-force trigger (Shadow Burst)
    total_g = (packet.imu.accel_x**2 + packet.imu.accel_y**2 + packet.imu.accel_z**2)**0.5

    if total_g > 2.5:
        await mnos_client.emit_event(
            "ss.vessel.shadow_burst",
            {
                "vessel_id": packet.vessel_id,
                "g_force": total_g,
                "location": {"lat": packet.gnss.latitude, "lon": packet.gnss.longitude},
                "imu_snapshot": packet.imu.model_dump()
            }
        )
        await mnos_client.push_to_shadow(
            packet.model_dump(),
            trace_id=f"burst-{uuid.uuid4()}"
        )

    return {
        "status": "RECEIVED",
        "total_g": round(total_g, 2),
        "comfort_score": comfort.score,
        "flight_state": packet.flight_state,
        "recommendation": comfort.recommendation if comfort.score >= 4.0 or "Transition" in (comfort.recommendation or "") else None
    }
