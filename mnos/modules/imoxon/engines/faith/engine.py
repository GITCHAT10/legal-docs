class FaithEngine:
    """
    Core: Muslim Companion.
    Integrates Prayer, Quran, Hadith, Dua, Qibla, Hijri, Tasbih.
    """
    def __init__(self, shadow, events):
        self.shadow = shadow
        self.events = events

    def trigger_prayer_reminder(self, prayer_name: str, island: str):
        payload = {"prayer": prayer_name, "island": island, "timestamp": "now"}
        self.events.publish("PRAYER_REMINDER_TRIGGERED", payload)

    def log_progress(self, user_id: str, activity_type: str, details: dict):
        # Progress for Quran, Tasbih, etc.
        log = {
            "user_id": user_id,
            "activity": activity_type,
            "details": details,
            "timestamp": "now"
        }
        self.shadow.commit("faith.progress", log)
        return True
