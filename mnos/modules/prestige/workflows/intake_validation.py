from typing import Dict, Any, Tuple
from mnos.modules.prestige.forms.uhnw_booking_template import UHNWBookingTemplate

class IntakeValidation:
    def validate_completion(self, intake: UHNWBookingTemplate) -> Tuple[bool, str]:
        """
        Completion rules:
        - privacy_level required
        - travel dates required
        - guest count required
        - arrival mode required
        - villa preference required
        - transfer preference required
        - budget band required
        - payment preference required
        - if private_jet selected, require jet logistics fields
        """
        if not intake.privacy_level: return False, "Missing privacy_level"
        if not intake.travel_dates: return False, "Missing travel_dates"
        if not intake.adults: return False, "Missing adults count"
        if not intake.arrival_mode: return False, "Missing arrival_mode"
        if not intake.villa_preference: return False, "Missing villa_preference"
        if not intake.transfer_preference: return False, "Missing transfer_preference"
        if not intake.budget_band: return False, "Missing budget_band"
        if not intake.payment_preference: return False, "Missing payment_preference"

        if intake.arrival_mode == "PRIVATE_JET":
            if not intake.private_jet_tail_no or not intake.eta:
                return False, "PRIVATE_JET requires tail_no and eta"

        return True, "COMPLETED"

    def check_escalation(self, intake: UHNWBookingTemplate) -> bool:
        # if P3/P4, trigger HUMAN_ESCALATION_REQUIRED
        return intake.privacy_level in ["P3", "P4"]
