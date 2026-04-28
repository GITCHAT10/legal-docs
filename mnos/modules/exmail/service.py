from datetime import datetime, UTC
from typing import Dict, List, Optional
import json

class EXMAILAutomationService:
    """
    EXMAIL: Resort Revenue Engine.
    Drives bookings and upsells via trigger-based automated sequences.
    """
    def __init__(self, core):
        self.core = core
        self.queue = []
        self.segment_logic = {
            "GCC": {"values": ["privacy", "luxury"], "tone": "formal"},
            "EUROPE": {"values": ["experience", "eco"], "tone": "inspirational"},
            "CHINA": {"values": ["speed", "clarity"], "tone": "direct"},
            "INDIA": {"values": ["bundle", "family"], "tone": "vibrant"}
        }

    def trigger_sequence(self, recipient_id: str, trigger_event: str, segment: str):
        """
        Main entry point for automated revenue sequences.
        """
        logic = self.segment_logic.get(segment, self.segment_logic["EUROPE"])

        # Build the offer contextually
        offer = self._build_contextual_offer(trigger_event, segment)

        sequence_id = f"SEQ-{recipient_id[:4]}-{trigger_event.upper()}"

        dispatch_item = {
            "id": sequence_id,
            "recipient": recipient_id,
            "trigger": trigger_event,
            "segment": segment,
            "offer": offer,
            "tone": logic["tone"],
            "queued_at": datetime.now(UTC).isoformat(),
            "status": "QUEUED"
        }

        self.queue.append(dispatch_item)
        self.core.events.publish("exmail.sequence_triggered", {"seq_id": sequence_id})

        return dispatch_item

    def _build_contextual_offer(self, trigger: str, segment: str):
        # The "Never Discount" Rule Application
        offers = {
            "abandoned_booking": {
                "incentive": "free_seaplane_transfer",
                "value": "$850",
                "psychology": "Remove Friction"
            },
            "price_drop": {
                "incentive": "villa_upgrade",
                "value": "$400/night",
                "psychology": "Aspirational Gain"
            },
            "repeat_visitor": {
                "incentive": "private_beach_dinner",
                "value": "$600",
                "psychology": "Recognition"
            }
        }
        return offers.get(trigger, {"incentive": "experience_bundle", "value": "$250"})

    def process_queue(self):
        processed = []
        for item in self.queue:
            if item["status"] == "QUEUED":
                item["status"] = "DISPATCHED"
                item["dispatched_at"] = datetime.now(UTC).isoformat()
                processed.append(item)

                # Audit to SHADOW
                self.core.shadow.commit(
                    "exmail.dispatch.success",
                    item["recipient"],
                    {"seq": item["id"], "offer": item["offer"]["incentive"]}
                )
        return processed
