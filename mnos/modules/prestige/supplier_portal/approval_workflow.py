import uuid
from typing import Dict, Any, List, Optional
from mnos.modules.prestige.supplier_portal.models import SupplierAction, AdminApprovalTask, FinanceReviewRecord, RevenueReviewRecord, CMOMarketStrategyProfile

class ApprovalWorkflowOrchestrator:
    """
    Orchestrates the multi-stage approval for supplier actions.
    Doctrine: Finance, Revenue, CMO, MAC EOS, FCE, SHADOW.
    """
    def __init__(self, core_system, config):
        self.core = core_system
        self.config = config
        self.tasks: Dict[str, AdminApprovalTask] = {}
        self.actions: Dict[str, SupplierAction] = {}

    def initiate_approval(self, action: SupplierAction) -> AdminApprovalTask:
        task_id = f"TASK-{uuid.uuid4().hex[:8].upper()}"

        required = ["FINANCE", "REVENUE", "CMO", "MAC_EOS", "FCE"]
        if action.action_type == "STOP_SELL":
             required = [] # Stop Sell is immediate for safety, but notified.

        task = AdminApprovalTask(
            task_id=task_id,
            action_id=action.action_id,
            required_approvals=required,
            current_stage=required[0] if required else "APPROVED"
        )
        self.tasks[task_id] = task
        self.actions[action.action_id] = action

        # SHADOW Seal
        self.core.shadow.commit("prestige.supplier.approval_initiated", action.submitted_by_actor_id, {
            "task_id": task_id,
            "action_id": action.action_id,
            "required": required
        })

        return task

    def record_decision(self, task_id: str, stage: str, actor_id: str, decision: str, data: Dict[str, Any]):
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError("Task not found")

        if stage != task.current_stage:
            raise ValueError(f"Task is currently at {task.current_stage}, not {stage}")

        task.approval_history.append({
            "stage": stage,
            "actor_id": actor_id,
            "decision": decision,
            "data": data,
            "timestamp": uuid.uuid4().hex # placeholder for real ts
        })

        if decision == "APPROVED":
            idx = task.required_approvals.index(stage)
            if idx < len(task.required_approvals) - 1:
                task.current_stage = task.required_approvals[idx + 1]
            else:
                task.current_stage = "COMPLETED"
                self.actions[task.action_id].status = "ACTIVE_FOR_SALE"
        else:
            task.current_stage = "REJECTED"
            self.actions[task.action_id].status = "REJECTED"

        # SHADOW Seal decision
        self.core.shadow.commit(f"prestige.supplier.{stage.lower()}_{decision.lower()}", actor_id, {
            "task_id": task_id,
            "decision": decision
        })

        return task
