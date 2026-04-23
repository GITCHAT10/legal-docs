from typing import Dict, Any, List

class ATCTowerService:
    """
    ATC Tower Service: Manages arrivals and transfers.
    Provides data for the SALA-OS Arrival Radar.
    """
    def get_arrival_radar_data(self) -> List[Dict[str, Any]]:
        # Simulation of radar data
        return [
            {"id": "FL-001", "type": "SEAPLANE", "eta": "14:30", "origin": "MLE"},
            {"id": "BT-005", "type": "SPEEDBOAT", "eta": "15:15", "origin": "RESORT-X"}
        ]

atc_tower = ATCTowerService()
