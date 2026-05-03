
NAMESPACE_MAPPING = {
    "QRD_MIG_SHIELD": "QRD",
    "ESG_TERRAFORM": "ESG",
    "WIFI_ROUTE": "WIFI",
    "ADMIRALDA": "ADMIRALDA",
    "ADMIRALDA_V2": "ADMIRALDA",
    "EXMAIL": "EXMAIL",
    "EXMAIL_V2": "EXMAIL",
    "MARS_PEOPLE": "PEOPLE",
    "MARS_PEOPLE_HR": "PEOPLE",
    "AIRBOX": "AIRBOX",
    "AIRBOX_EDGE": "AIRBOX",
    "AIRCLOUD": "AIRCLOUD",
    "AIRCLOUD_SYNC": "AIRCLOUD",
    "TENANT_ISOLATION_GATE": "ISOLATION"
}

def get_logical_prefix(system: str) -> str:
    return NAMESPACE_MAPPING.get(system)

def validate_namespace(system: str, event_type: str) -> bool:
    if system in ["CORE", "EDGE_NODE"]:
        return True

    prefix = get_logical_prefix(system)
    if not prefix:
        # If not in mapping, we might allow it if it matches vertical names directly or through other rules
        # but the requirement says "Add allOf namespace guards" for specific ones.
        return True

    return event_type.startswith(f"{prefix}.")
