from datetime import datetime, timezone
from typing import Dict, Any, Optional

class ApprovalRequired(Exception):
    """Exception raised when an action requires supervisor approval."""
    pass

def require_supervisor_approval(action: str, operator_id: Optional[str]) -> Dict[str, Any]:
    """
    Mandatory human approval control layer.
    AI remains ADVISORY_ONLY and cannot trigger state-changing actions without an operator.
    """
    if not operator_id or not operator_id.strip():
        raise ApprovalRequired(f"Action '{action}' requires a valid supervisor operator_id.")

    return {
        "status": "APPROVED",
        "approved_by": operator_id,
        "action": action,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
