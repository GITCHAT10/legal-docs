from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
from mnos.modules.shadow.service import shadow

class CaseStatus(Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    HEARING = "HEARING"
    CLOSED = "CLOSED"
    APPEAL = "APPEAL"

class CaseCategory(Enum):
    CIVIL = "CIVIL"
    CRIMINAL = "CRIMINAL"
    CORPORATE = "CORPORATE"
    LAND = "LAND"
    EMPLOYMENT = "EMPLOYMENT"

class MatterManager:
    """
    eLEGAL Case and Matter Management (Adopting InfixAdvocate features).
    Tracks court schedules, statuses, and legal categories for the enterprise.
    """
    def __init__(self):
        self.cases: Dict[str, Dict[str, Any]] = {}

    def create_case(self, case_id: str, title: str, category: CaseCategory, client_id: str) -> Dict[str, Any]:
        case_data = {
            "case_id": case_id,
            "title": title,
            "category": category.value,
            "client_id": client_id,
            "status": CaseStatus.PENDING.value,
            "created_at": datetime.now().isoformat(),
            "hearings": [],
            "documents": []
        }
        self.cases[case_id] = case_data
        shadow.commit("elegal.case.updated", {"action": "CREATE", "case_id": case_id, "data": case_data})
        return case_data

    def schedule_hearing(self, case_id: str, hearing_date: str, courtroom: str) -> Dict[str, Any]:
        if case_id not in self.cases:
            raise ValueError(f"Case {case_id} not found.")

        hearing = {
            "date": hearing_date,
            "courtroom": courtroom,
            "status": "SCHEDULED"
        }
        self.cases[case_id]["hearings"].append(hearing)
        self.cases[case_id]["status"] = CaseStatus.HEARING.value

        shadow.commit("elegal.case.updated", {"action": "SCHEDULE_HEARING", "case_id": case_id, "hearing": hearing})
        return self.cases[case_id]

    def update_status(self, case_id: str, status: CaseStatus) -> Dict[str, Any]:
        if case_id not in self.cases:
            raise ValueError(f"Case {case_id} not found.")

        self.cases[case_id]["status"] = status.value
        shadow.commit("elegal.case.updated", {"action": "UPDATE_STATUS", "case_id": case_id, "status": status.value})
        return self.cases[case_id]

matter_manager = MatterManager()
