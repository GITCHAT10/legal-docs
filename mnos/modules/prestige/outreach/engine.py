import datetime
import uuid
from mnos.modules.prestige.models import OutreachContact

class OutreachEngine:
    def __init__(self, core_system):
        self.core = core_system
        self.approval_records = {} # approval_id -> record

    async def process_outreach(self, actor_ctx: dict, contact_data: dict):
        contact = OutreachContact.from_csv_row(contact_data)

        # Rule: No Priority A high-score contact should be auto-sent without approval.
        if contact.requires_approval:
            return await self.queue_for_approval(actor_ctx, contact)

        return await self.send_outreach(actor_ctx, contact)

    async def queue_for_approval(self, actor_ctx: dict, contact: OutreachContact):
        # Full ExecutionGuard enforcement for mutating outreach actions
        return self.core.guard.execute_sovereign_action(
            "prestige.outreach.queue_approval",
            actor_ctx,
            self._internal_queue_for_approval,
            contact
        )

    def _internal_queue_for_approval(self, contact: OutreachContact):
        approval_id = f"APP-{uuid.uuid4().hex[:8].upper()}"
        actor = self.core.guard.get_actor()
        actor_id = actor.get("identity_id") if actor else "SYSTEM"

        record = {
            "approval_id": approval_id,
            "contact_id": contact.contact_id,
            "actor_id": actor_id,
            "payload": contact.model_dump(),
            "status": "PENDING",
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "trace_id": uuid.uuid4().hex
        }

        self.approval_records[approval_id] = record

        # SHADOW event - Attribution to authorized actor
        self.core.shadow.commit("prestige.outreach.pending_approval", actor_id, record)

        return {"status": "pending_human_approval", "approval_id": approval_id, "contact_id": contact.contact_id}

    async def approve_and_send(self, actor_ctx: dict, approval_id: str, approver_id: str):
        return self.core.guard.execute_sovereign_action(
            "prestige.outreach.approve",
            actor_ctx,
            self._internal_approve_and_send,
            approval_id, approver_id
        )

    def _internal_approve_and_send(self, approval_id: str, approver_id: str):
        record = self.approval_records.get(approval_id)
        if not record:
            raise ValueError("Invalid approval_id")

        if record["status"] != "PENDING":
            raise ValueError(f"Approval ID {approval_id} already processed (status: {record['status']})")

        record["status"] = "APPROVED"
        record["approver_id"] = approver_id
        record["approved_at"] = datetime.datetime.now(datetime.UTC).isoformat()

        # SHADOW-sealed approval event
        self.core.shadow.commit("prestige.outreach.approved", approver_id, record)

        return {"status": "sent", "approval_record": record}

    async def reject_outreach(self, actor_ctx: dict, approval_id: str, approver_id: str):
         return self.core.guard.execute_sovereign_action(
            "prestige.outreach.reject",
            actor_ctx,
            self._internal_reject,
            approval_id, approver_id
        )

    def _internal_reject(self, approval_id: str, approver_id: str):
        record = self.approval_records.get(approval_id)
        if not record:
            raise ValueError("Invalid approval_id")

        if record["status"] != "PENDING":
            raise ValueError(f"Approval ID {approval_id} already processed")

        record["status"] = "REJECTED"
        record["approver_id"] = approver_id
        record["rejected_at"] = datetime.datetime.now(datetime.UTC).isoformat()

        self.core.shadow.commit("prestige.outreach.rejected", approver_id, record)
        return {"status": "rejected", "approval_id": approval_id}

    async def send_outreach(self, actor_ctx: dict, contact: OutreachContact):
        return self.core.guard.execute_sovereign_action(
            "prestige.outreach.send",
            actor_ctx,
            self._internal_send_outreach,
            contact
        )

    def _internal_send_outreach(self, contact: OutreachContact):
        actor = self.core.guard.get_actor()
        actor_id = actor.get("identity_id") if actor else "SYSTEM"

        send_event = {
            "contact_id": contact.contact_id,
            "email": contact.email,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "pdpa_compliance": True,
            "unsubscribe_link": f"https://prestige.mv/unsubscribe/{contact.contact_id}"
        }
        self.core.shadow.commit("prestige.outreach.sent", actor_id, send_event)
        return {"status": "sent", "contact_id": contact.contact_id}
