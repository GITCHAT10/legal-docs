from typing import List, Dict, Any
from pydantic import BaseModel, Field

class SmartEnvironment(BaseModel):
    energy_source: str = "Solar/Battery Hybrid"
    solar_capacity_kw: float
    battery_storage_kwh: float
    water_system: str = "RO Desalination + Rainwater"
    smart_hubs: int
    ac_units_sheddable: int

def configure_euper_ai(floor_area_sqm: float, rooms: int, terrace_area_sqm: float) -> SmartEnvironment:
    """
    EUPER AI NEXT GEN: Maldives Smart Building Engine.
    Optimizes energy and utilities for island-based operations.
    Inspired by MARS Architecture but hardened for Maldives Sovereign OS.
    """
    # 1. Solar Potential (Terrace usage)
    # 1 sqm of solar approx 0.2 kW. Use 60% of terrace.
    solar_kw = (terrace_area_sqm * 0.6) * 0.2

    # 2. Battery Storage (Heuristic: 4 hours of backup)
    # Avg hotel room in Maldives uses ~2kW with AC.
    avg_load_kw = rooms * 1.5
    battery_kwh = avg_load_kw * 4

    # 3. MARS Smart Hubs
    # 1 per floor + 1 per room
    hubs = 1 + rooms

    return SmartEnvironment(
        solar_capacity_kw=round(solar_kw, 2),
        battery_storage_kwh=round(battery_kwh, 2),
        smart_hubs=hubs,
        ac_units_sheddable=rooms
    )

def get_euper_automation_rules() -> List[Dict[str, Any]]:
    """
    MARS Intelligent automation rules for Maldives conditions.
    """
    return [
        {
            "name": "Monsoon Energy Guard",
            "trigger": "Solar output < 10% for 2 hours",
            "action": "Disable non-essential AC in common areas, activate battery reserve"
        },
        {
            "name": "Desalination Sync",
            "trigger": "Battery level > 90% (Excess Solar)",
            "action": "Activate RO Desalination plant to fill water tanks"
        },
        {
            "name": "Rainwater Harvest Switch",
            "trigger": "Precipitation detected > 5mm/h",
            "action": "Divert roof runoff to secondary filtration tanks"
        }
    ]
