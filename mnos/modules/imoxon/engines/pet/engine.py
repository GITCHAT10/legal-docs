class PetEngine:
    def __init__(self, shadow, events):
        self.shadow = shadow
        self.events = events

    def book_vet(self, user_id: str, pet_id: str, clinic_id: str, time: str):
        booking = {
            "user_id": user_id,
            "pet_id": pet_id,
            "clinic_id": clinic_id,
            "time": time,
            "status": "BOOKED"
        }
        self.shadow.commit("pet.vet_booked", booking)
        self.events.publish("VET_BOOKED", booking)
        return booking

    def aquarium_fish_care_log(self, user_id: str, task: str):
        self.shadow.commit("pet.fish_care", {"user": user_id, "task": task})
