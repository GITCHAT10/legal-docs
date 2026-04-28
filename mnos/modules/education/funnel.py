from datetime import datetime, UTC
from typing import Dict, List, Optional
import uuid

class UHAQualificationFunnel:
    """
    UHA Talent Engine: Self-Funding Sovereign Flywheel
    Flow: Ad -> Free -> Email -> Qualification -> Accelerator -> Deployment
    """
    def __init__(self, core):
        self.core = core
        self.leads = {} # lead_id -> data

    def capture_lead(self, email: str, source: str = "meta_ads"):
        lead_id = str(uuid.uuid4())[:8].upper()
        lead = {
            "lead_id": lead_id,
            "email": email,
            "source": source,
            "intent_score": 10, # Baseline for click
            "stage": "FREE_CONTENT",
            "captured_at": datetime.now(UTC).isoformat(),
            "engagements": []
        }
        self.leads[lead_id] = lead
        return lead

    def record_engagement(self, lead_id: str, action: str):
        lead = self.leads.get(lead_id)
        if not lead: return None

        # Scoring logic
        scores = {
            "video_watch_50": 15,
            "video_watch_100": 30,
            "syllabus_download": 20,
            "quiz_completed": 40,
            "booking_page_visit": 50
        }

        impact = scores.get(action, 5)
        lead["intent_score"] = min(100, lead["intent_score"] + impact)
        lead["engagements"].append({"action": action, "at": datetime.now(UTC).isoformat()})

        # Auto-Qualification Trigger
        if lead["intent_score"] > 85 and lead["stage"] == "FREE_CONTENT":
            lead["stage"] = "QUALIFIED"
            self.core.events.publish("uha.lead.qualified", {"lead_id": lead_id, "score": lead["intent_score"]})

        return lead

    def get_offer(self, lead_id: str):
        lead = self.leads.get(lead_id)
        if not lead: return None

        score = lead["intent_score"]

        if score > 85:
            return {"offer": "upgrade + urgency", "cta": "Apply for Accelerator (Limited Seats)", "discount_code": "ELITE-2026"}
        elif score > 70:
            return {"offer": "free_transfer_guarantee", "cta": "Reserve your spot", "value_stack": "$850"}
        else:
            return {"offer": "experience_bundle", "cta": "Watch Masterclass"}

    def qualify_candidate(self, lead_id: str, application_data: dict):
        lead = self.leads.get(lead_id)
        if not lead: return None

        # Logic to move to Accelerator
        lead["stage"] = "ACCELERATOR_PENDING"
        lead["application"] = application_data

        self.core.events.publish("uha.application.submitted", {"lead_id": lead_id})
        return lead
