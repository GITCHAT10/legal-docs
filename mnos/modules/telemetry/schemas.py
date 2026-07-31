from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, List, Dict
from enum import Enum

class FlightState(str, Enum):
    DISPLACEMENT = "DISPLACEMENT"
    TRANSITION = "TRANSITION"
    FOILING = "FOILING"

class HandshakeRequest(BaseModel):
    vessel_id: str
    kit_serial: str
    firmware_version: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class HandshakeResponse(BaseModel):
    status: str
    session_token: str
    heartbeat_interval_seconds: int = 5
    config: dict = {}

class IMUData(BaseModel):
    pitch: float  # Degrees
    roll: float   # Degrees
    yaw: float    # Degrees
    accel_x: float # G
    accel_y: float # G
    accel_z: float # G
    vibration_frequency: float # Hz
    vibration_amplitude: float # mm/s

class GNSSData(BaseModel):
    latitude: float
    longitude: float
    altitude: float
    speed: float # knots
    course: float # degrees
    satellites: int

class ActuatorData(BaseModel):
    flap_angle: float # degrees
    strut_extension: float # percentage 0-100
    motor_rpm: int
    power_draw_kw: float

class TelemetryPacket(BaseModel):
    vessel_id: str
    session_token: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    imu: IMUData
    gnss: GNSSData
    actuators: Optional[ActuatorData] = None
    flight_state: FlightState = FlightState.DISPLACEMENT
    flying_height: float = 0.0 # meters
    wave_height: float = 0.0 # meters
    battery_voltage: float
    is_charging: bool

class ComfortIndex(BaseModel):
    vessel_id: str
    score: float = Field(..., ge=0.0, le=10.0) # 0.0 (Perfect) to 10.0 (Extreme)
    pitch_stability: float
    roll_stability: float
    vibration_level: float
    flight_efficiency: float # 0-1.0
    status: str # "SMOOTH", "MODERATE", "ROUGH", "EXTREME"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    recommendation: Optional[str] = None
