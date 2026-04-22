from typing import List, Dict, Any
from datetime import datetime
from mnos.modules.shadow.service import shadow

class ClientManager:
    """
    eLEGAL Client and Appointment Management (Adopting InfixAdvocate features).
    Manages client records and appointments across the enterprise.
    """
    def __init__(self):
        self.clients: Dict[str, Dict[str, Any]] = {}
        self.appointments: List[Dict[str, Any]] = []

    def register_client(self, client_id: str, name: str, brand: str, contact: str) -> Dict[str, Any]:
        client_data = {
            "client_id": client_id,
            "name": name,
            "brand": brand,
            "contact": contact,
            "joined_at": datetime.now().isoformat()
        }
        self.clients[client_id] = client_data
        shadow.commit("elegal.entity.registered", client_data)
        return client_data

    def schedule_appointment(self, client_id: str, date: str, purpose: str) -> Dict[str, Any]:
        if client_id not in self.clients:
            raise ValueError(f"Client {client_id} not found.")

        appointment = {
            "client_id": client_id,
            "client_name": self.clients[client_id]["name"],
            "date": date,
            "purpose": purpose,
            "status": "SCHEDULED"
        }
        self.appointments.append(appointment)
        shadow.commit("elegal.appointment.scheduled", appointment)
        return appointment

client_manager = ClientManager()
