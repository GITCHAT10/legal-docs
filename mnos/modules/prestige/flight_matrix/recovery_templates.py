from mnos.modules.prestige.flight_matrix.models import RecoveryOption

RECOVERY_TEMPLATES = {
    "LATE_SEAPLANE_RECOVERY": RecoveryOption(
        template_id="LATE_SEAPLANE_RECOVERY",
        description="Overnight near Velana International Airport followed by morning seaplane transfer.",
        night_1_stay="Malé / Hulhumalé airport-area stay",
        day_2_transfer="Morning seaplane transfer",
        tone="Controlled daylight island arrival for safety, comfort, and service precision."
    ),
    "DOMESTIC_CONNECTION_RECOVERY": RecoveryOption(
        template_id="DOMESTIC_CONNECTION_RECOVERY",
        description="Overnight stay near airport to catch the first domestic connection the next day.",
        night_1_stay="Malé / Hulhumalé",
        day_2_transfer="First suitable domestic flight + onward boat transfer",
        tone="Optimized connection timing to ensure arrival quality and villa-readiness."
    ),
    "UNSAFE_NIGHT_SPEEDBOAT_RECOVERY": RecoveryOption(
        template_id="UNSAFE_NIGHT_SPEEDBOAT_RECOVERY",
        description="Safety-first overnight stay due to adverse sea conditions or late hour.",
        night_1_stay="Overnight near airport",
        day_2_transfer="Morning speedboat",
        tone="We recommend a controlled daylight island arrival for safety, comfort, and service precision."
    ),
    "ALTERNATIVE_RESORT_PIVOT": RecoveryOption(
        template_id="ALTERNATIVE_RESORT_PIVOT",
        description="Switch to a resort reachable by speedboat on the same day.",
        night_1_stay="N/A",
        day_2_transfer="N/A",
        tone="To ensure immediate island arrival, we suggest an alternative premium stay reachable within our safe transit window."
    )
}

def get_recovery_template(reason: str) -> RecoveryOption:
    if "SEAPLANE_CUTOFF" in reason:
        return RECOVERY_TEMPLATES["LATE_SEAPLANE_RECOVERY"]
    if "DOMESTIC_CONNECTION" in reason:
        return RECOVERY_TEMPLATES["DOMESTIC_CONNECTION_RECOVERY"]
    if "UNSAFE_NIGHT_SPEEDBOAT" in reason:
        return RECOVERY_TEMPLATES["UNSAFE_NIGHT_SPEEDBOAT_RECOVERY"]
    return RECOVERY_TEMPLATES["ALTERNATIVE_RESORT_PIVOT"]

def get_brief_tone(guest_segment: str, recovery_tone: str) -> str:
    if guest_segment == "UHNW":
         return ("To ensure a smooth and private arrival experience, Prestige Holidays recommends a "
                 "controlled first-night arrival near Velana International Airport, followed by a "
                 "daylight transfer to your island resort the next morning.")
    return recovery_tone
