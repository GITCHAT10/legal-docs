from typing import Dict, List

COMPLIANCE_REGISTRY = {
    "MV": {
        "mndf_approval_required": True,
        "caa_permit_required": True,
        "privacy_zones_required": True,
        "max_altitude_m": 120
    },
    "PH": {
        "disaster_agency_sync": True,
        "caap_permit_required": True,
        "coastal_authority_sync": True
    },
    "AU": {
        "casa_compliance_required": True,
        "emergency_services_link": True,
        "data_retention_policy_enforced": True
    }
}

def get_compliance_for_country(country_code: str) -> dict:
    return COMPLIANCE_REGISTRY.get(country_code, {"basic_aviation_permit": True})
