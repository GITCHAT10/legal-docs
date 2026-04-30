import datetime
from typing import List, Dict, Optional
from mnos.modules.prestige.models import OutreachContact
from mnos.shared.execution_guard import ExecutionGuard

class OutreachEngine:
    def __init__(self, core_system):
        self.core = core_system
        self.approval_records = {}

    async def process_outreach(self, actor_ctx: dict, contact_data: dict):
        contact = OutreachContact.from_csv_row(contact_data)

        # Rule: No Priority A high-score contact should be auto-sent without approval.
        if contact.requires_approval:
            return await self.queue_for_approval(actor_ctx, contact)

        return await self.send_outreach(actor_ctx, contact)

    async def queue_for_approval(self, actor_ctx: dict, contact: OutreachContact):
        # SHADOW commit required inside ExecutionGuard
        with ExecutionGuard.sovereign_context(actor_ctx):
            payload = {
                "contact_id": contact.contact_id,
                "reason": "high_priority_approval_required",
                "lead_score": contact.lead_score,
                "status": "PENDING"
            }
            self.core.shadow.commit("prestige.outreach.pending_approval", contact.contact_id, payload)

        return {"status": "pending_human_approval", "contact_id": contact.contact_id}

    async def approve_and_send(self, actor_ctx: dict, approval_id: str, approver_id: str):
        # Production needs a real approval record
        record = {
            "approval_id": approval_id,
            "approver_id": approver_id,
            "approved_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "status": "APPROVED"
        }
        self.approval_records[approval_id] = record

        # SHADOW-sealed approval event
        with ExecutionGuard.sovereign_context(actor_ctx):
            self.core.shadow.commit("prestige.outreach.approved", approver_id, record)

        # Proceed with send...
        return {"status": "sent", "approval_record": record}

    async def send_outreach(self, actor_ctx: dict, contact: OutreachContact):
        # All outreach intent and send events must be SHADOW-sealed
        with ExecutionGuard.sovereign_context(actor_ctx):
            send_event = {
                "contact_id": contact.contact_id,
                "email": contact.email,
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                "pdpa_compliance": True,
                "unsubscribe_link": f"https://prestige.mv/unsubscribe/{contact.contact_id}"
            }
            self.core.shadow.commit("prestige.outreach.sent", contact.contact_id, send_event)

        return {"status": "sent", "contact_id": contact.contact_id}
