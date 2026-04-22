class HealthEngine:
    def __init__(self, shadow, events):
        self.shadow = shadow
        self.events = events
        self.appointments = {}

    def book_doctor(self, user_id: str, clinic_id: str, doctor_id: str, time: str):
        apt_id = f"apt_{hash(user_id + doctor_id + time) % 10000}"
        appointment = {
            "apt_id": apt_id,
            "user_id": user_id,
            "clinic_id": clinic_id,
            "doctor_id": doctor_id,
            "time": time,
            "status": "BOOKED"
        }
        self.shadow.record_action("appointment.booked", appointment)
        self.events.trigger("APPOINTMENT_BOOKED", appointment)
        self.appointments[apt_id] = appointment
        return appointment
