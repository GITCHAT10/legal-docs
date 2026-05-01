from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class ShadowReportProfile:
    report_type: str
    export_format: List[str] = field(default_factory=lambda: ["PDF", "JSON"])
    required_fields: List[str] = field(default_factory=lambda: [
        "incident_id", "country_profile", "authority_chain",
        "camera_ids", "drone_ids", "operator_ids", "timestamp_chain",
        "evidence_refs", "privacy_masking_status", "ORCA_snapshot",
        "AEGIS_snapshot", "SHADOW_hash"
    ])
    include_orca_snapshot: bool = True
    include_aegis_snapshot: bool = True
    include_privacy_status: bool = True

REPORT_PROFILES: Dict[str, ShadowReportProfile] = {
    "RESORT_INCIDENT_REPORT": ShadowReportProfile("RESORT_INCIDENT_REPORT"),
    "DROWNING_RESPONSE_REPORT": ShadowReportProfile("DROWNING_RESPONSE_REPORT"),
    "MEDICAL_RESPONSE_REPORT": ShadowReportProfile("MEDICAL_RESPONSE_REPORT"),
    "FIRE_SMOKE_REPORT": ShadowReportProfile("FIRE_SMOKE_REPORT"),
    "MISSING_PERSON_REPORT": ShadowReportProfile("MISSING_PERSON_REPORT"),
    "CROWD_RISK_REPORT": ShadowReportProfile("CROWD_RISK_REPORT"),
    "TRAFFIC_INCIDENT_REPORT": ShadowReportProfile("TRAFFIC_INCIDENT_REPORT"),
    "MARITIME_INCIDENT_REPORT": ShadowReportProfile("MARITIME_INCIDENT_REPORT"),
    "DISASTER_DAMAGE_REPORT": ShadowReportProfile("DISASTER_DAMAGE_REPORT"),
    "POLICE_CASE_EVIDENCE_EXPORT": ShadowReportProfile("POLICE_CASE_EVIDENCE_EXPORT", required_fields=[
        "case_id", "incident_id", "evidence_refs", "SHADOW_hash"
    ]),
    "MNDF_NATIONAL_SECURITY_EVENT": ShadowReportProfile("MNDF_NATIONAL_SECURITY_EVENT"),
    "COMPLIANCE_READINESS_REPORT": ShadowReportProfile("COMPLIANCE_READINESS_REPORT")
}
