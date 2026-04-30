from datetime import datetime, timedelta, UTC
from typing import List, Dict, Any, Optional
from mnos.modules.prestige.dashboards.status_models import ArrivalRecord, CommandStatus

class CommandCenter:
    def __init__(self, shadow, escalation_playbook):
        self.shadow = shadow
        self.escalation = escalation_playbook
        self.arrivals: Dict[str, ArrivalRecord] = {}

    def ingest_arrival(self, record: ArrivalRecord):
        self.arrivals[record.booking_id] = record

    def get_status(self, booking_id: str) -> CommandStatus:
        record = self.arrivals.get(booking_id)
        if not record: return CommandStatus.GREEN

        # Logic: missing final 24h seal prevents GREEN
        if not record.logistics_seal and record.status == CommandStatus.GREEN:
            return CommandStatus.YELLOW

        return record.status

    def calculate_global_status(self, current_time: datetime = None) -> List[ArrivalRecord]:
        """72-hour arrivals view logic."""
        if not current_time: current_time = datetime.now(UTC)
        window_end = current_time + timedelta(hours=72)

        view = []
        for record in self.arrivals.values():
            if current_time <= record.arrival_time <= window_end:
                # Logic: RED within 24h triggers MAC EOS escalation
                time_to_arrival = record.arrival_time - current_time
                if record.status == CommandStatus.RED and time_to_arrival <= timedelta(hours=24):
                     self.escalation.open_escalation(record.booking_id, "CRITICAL_RED_WITHIN_24H", {"identity_id": "SYSTEM"})

                view.append(record)
        return view

    def safe_view(self, booking_id: str) -> Dict[str, Any]:
        """Dashboard safe view hides sensitive data."""
        record = self.arrivals.get(booking_id)
        if not record: return {}

        data = record.model_dump()
        if record.privacy_level in ["P3", "P4"]:
            data.pop("guest_name", None)
            data["guest_name"] = "REDACTED"
            data["issues"] = ["SENSITIVE_ISSUE_PENDING"] if record.status != CommandStatus.GREEN else []

        return data

    def block_auto_recovery(self, booking_id: str, issue_type: str) -> bool:
        """P3/P4 RED transfer/villa/security issue blocks auto-recovery."""
        record = self.arrivals.get(booking_id)
        if not record: return False

        if record.privacy_level in ["P3", "P4"]:
            if issue_type in ["transfer", "villa", "security"]:
                return True
        return False
