"""
MNOS Sovereign Constitution - Global Mapping
Legal Root: MALDIVES INTERNATIONAL GROUP PVT LTD (UEI: 2024PV12395H)
"""

from typing import Dict

CONSTITUTION: Dict[str, str] = {
    "LEGAL_ROOT": "MALDIVES INTERNATIONAL GROUP PVT LTD",
    "UEI": "2024PV12395H",
    "JURISDICTION": "MALDIVES",
    "DOCTRINE": "SOVEREIGN_CORE_V1.1_FORTRESS"
}

def get_legal_root() -> str:
    return f"{CONSTITUTION['LEGAL_ROOT']} (UEI: {CONSTITUTION['UEI']})"
