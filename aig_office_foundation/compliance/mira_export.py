import json
from datetime import datetime, UTC
from typing import List

class MiraExportEngine:
    """
    MIRA-Ready Financial Audit Export.
    Aggregates financial events for tax reporting.
    """
    def __init__(self, shadow_ledger):
        self.shadow_ledger = shadow_ledger

    def generate_mira_report(self, start_date: str, end_date: str) -> dict:
        """
        Filters the SHADOW ledger for financial events and formats for MIRA.
        """
        financial_events = [
            b["data"] for b in self.shadow_ledger.ledger
            if b["data"]["event_type"].startswith("finance.")
            and start_date <= b["data"]["timestamp"] <= end_date
        ]

        report = {
            "report_id": f"MIRA-AUDIT-{datetime.now(UTC).strftime('%Y%m%d')}",
            "period": {"start": start_date, "end": end_date},
            "record_count": len(financial_events),
            "records": financial_events,
            "forensic_hash": self.shadow_ledger.chain.last_hash
        }

        return report
