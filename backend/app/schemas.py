from pydantic import BaseModel, Field
from typing import Optional

class HomeInput(BaseModel):
    electricity_kwh: float = Field(0, ge=0)
    water_m3: float = Field(0, ge=0)
    lpg_kg: float = Field(0, ge=0)

class TransportInput(BaseModel):
    petrol_car_km: float = Field(0, ge=0)
    diesel_car_km: float = Field(0, ge=0)
    motorcycle_km: float = Field(0, ge=0)
    speedboat_liters: float = Field(0, ge=0)
    ferry_km: float = Field(0, ge=0)
    seaplane_km: float = Field(0, ge=0)
    domestic_flight_km: float = Field(0, ge=0)

class WasteInput(BaseModel):
    waste_kg: float = Field(0, ge=0)

class FootprintInput(BaseModel):
    home: Optional[HomeInput] = None
    transport: Optional[TransportInput] = None
    waste: Optional[WasteInput] = None

class FootprintResult(BaseModel):
    home_total: float
    transport_total: float
    waste_total: float
    grand_total: float
