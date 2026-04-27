import uuid
from typing import Dict, List, Any

class OrcaSalesEngine:
    """
    ORCA Sales Engine: CRM & Sales Task Orchestration.
    Manages lead status and sales representative workflows.
    """
    def __init__(self, shadow, guard):
        self.shadow = shadow
        self.guard = guard
        self.leads = {} # email -> status
        self.tasks = []

    def update_lead_status(self, email: str, status: str):
        self.leads[email] = status
        print(f"[ORCA SALES] Lead {email} updated to {status}")

        # This is typically called within an existing context in this task
        self.shadow.commit("sales.lead.updated", "SYSTEM", {
            "email": email,
            "status": status
        })

    def create_sales_task(self, email: str, task_type: str, assignee: str, priority: str):
        task = {
            "task_id": f"TSK-{uuid.uuid4().hex[:6].upper()}",
            "email": email,
            "type": task_type,
            "assignee": assignee,
            "priority": priority,
            "status": "OPEN"
        }
        self.tasks.append(task)
        print(f"[ORCA SALES] Task {task['task_id']} created for {assignee}")

        self.shadow.commit("sales.task.created", "SYSTEM", task)
        return task

    def get_tasks_for(self, assignee: str) -> List[dict]:
        return [t for t in self.tasks if t["assignee"] == assignee]
