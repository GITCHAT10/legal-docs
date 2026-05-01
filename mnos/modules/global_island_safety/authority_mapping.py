from typing import Dict, List

AUTHORITY_MAPPING = {
    "MV": {
        "DRONE_LAUNCH": "MNDF",
        "AIRSPACE": "Maldives CAA",
        "PUBLIC_SAFETY": "Police",
        "EVIDENCE_ACCESS": "Police (Case-based)",
        "DISASTER_RESPONSE": "NDMA"
    },
    "AU": {
        "DRONE_LAUNCH": "CASA",
        "PUBLIC_SAFETY": "State Police",
        "EMERGENCY_SERVICES": "SES / Fire Agencies",
        "DATA_GOVERNANCE": "Privacy Commissioner"
    }
}

def get_authority_for_action(country_code: str, action: str) -> str:
    return AUTHORITY_MAPPING.get(country_code, {}).get(action, "Local Authority")
