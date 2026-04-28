from datetime import datetime, UTC
from typing import Dict, List, Optional

class PostStayLoyaltyLoop:
    """
    Creates compounding revenue via review-for-reward and referral loops.
    """
    def __init__(self, core):
        self.core = core
        self.rewards = {
            "review": "private_beach_dinner",
            "referral": "loyalty_points_1000",
            "return_stay": "villa_upgrade_guaranteed"
        }

    def trigger_post_stay_email(self, guest_id: str, resort_id: str):
        """
        Triggered when guest checks out.
        """
        event = {
            "guest_id": guest_id,
            "resort_id": resort_id,
            "action": "loyalty_activation",
            "offers": [
                {"action": "submit_review", "reward": self.rewards["review"]},
                {"action": "refer_friend", "reward": self.rewards["referral"]}
            ],
            "triggered_at": datetime.now(UTC).isoformat()
        }

        self.core.events.publish("loyalty.loop_triggered", event)
        return event

    def process_referral(self, referrer_id: str, friend_email: str):
        """
        Processes a referral to grow the demand engine.
        """
        # Audit to SHADOW
        self.core.shadow.commit(
            "loyalty.referral.recorded",
            referrer_id,
            {"referral_email": friend_email, "status": "PENDING_ACQUISITION"}
        )

        return {"status": "SUCCESS", "reward_pending": self.rewards["referral"]}
