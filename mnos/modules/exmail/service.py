import uuid
from datetime import datetime, UTC
from typing import Dict, List, Any
from .schemas import EmailEvent, ExmailStats

class ExMailService:
    def __init__(self, guard, shadow, events, orca_sales, mailchimp_adapter):
        self.guard = guard
        self.shadow = shadow
        self.events = events
        self.orca_sales = orca_sales
        self.adapter = mailchimp_adapter
        self.stats = {
            "emails_sent": 0,
            "opens": 0,
            "clicks": 0,
            "replies": 0
        }

    def send_campaign(self, actor_ctx: dict, campaign_name: str, recipients: list):
        trace_id = f"EXM-CMP-{uuid.uuid4().hex[:6].upper()}"
        with self.guard.sovereign_context(trace_id=trace_id):
            res = self.adapter.send_campaign(campaign_name, recipients)
            self.stats["emails_sent"] += len(recipients)
            self.shadow.commit("exmail.campaign.sent", actor_ctx["identity_id"], {
                "campaign": campaign_name,
                "count": len(recipients),
                "trace_id": trace_id
            })
            return res

    def process_outbound_mail(self, actor_ctx: dict, message_data: dict):
        """Unified interface for sending transactional emails."""
        trace_id = f"EXM-TX-{uuid.uuid4().hex[:6].upper()}"
        with self.guard.sovereign_context(trace_id=trace_id):
            # For transactional, we can reuse the adapter's logic or a separate one
            # Here we simulate by adding to stats and logging
            self.stats["emails_sent"] += 1
            self.shadow.commit("exmail.transactional.sent", actor_ctx["identity_id"], {
                "to": message_data.get("to"),
                "subject": message_data.get("subject"),
                "trace_id": trace_id
            })
            return f"msg_{uuid.uuid4().hex[:8]}"

    def process_webhook_event(self, raw_event: dict):
        event = self.adapter.normalize_event(raw_event)
        trace_id = f"EXM-WEB-{uuid.uuid4().hex[:6].upper()}"

        # Identity for webhook is SYSTEM since it comes from external
        from mnos.shared.execution_guard import ExecutionGuard
        with ExecutionGuard.sovereign_context(trace_id=trace_id):
            self.log_email_event(event, trace_id)
            self._update_stats(event.event)
            self._trigger_crm_integration(event)

        return {"status": "processed", "trace_id": trace_id}

    def log_email_event(self, event: EmailEvent, trace_id: str):
        self.shadow.commit(f"exmail.event.{event.event}", "SYSTEM", {
            "email": event.email,
            "campaign": event.campaign,
            "trace_id": trace_id
        })

    def _update_stats(self, event_type: str):
        if event_type == "opened": self.stats["opens"] += 1
        elif event_type == "clicked": self.stats["clicks"] += 1
        elif event_type == "replied": self.stats["replies"] += 1

    def _trigger_crm_integration(self, event: EmailEvent):
        # CRM Mapping logic
        status_map = {
            "opened": "CONTACTED",
            "clicked": "ENGAGED",
            "replied": "IN TALKS"
        }
        new_status = status_map.get(event.event)
        if new_status:
            self.orca_sales.update_lead_status(event.email, new_status)

        if event.event == "replied":
            self.orca_sales.create_sales_task(
                email=event.email,
                task_type="FOLLOW_UP",
                assignee="Irina Rogova",
                priority="HIGH"
            )

    def get_stats(self) -> ExmailStats:
        total = self.stats["emails_sent"]
        conv_rate = (self.stats["replies"] / total * 100) if total > 0 else 0.0
        return ExmailStats(
            emails_sent=total,
            opens=self.stats["opens"],
            clicks=self.stats["clicks"],
            replies=self.stats["replies"],
            conversion_rate=round(conv_rate, 2)
        )
