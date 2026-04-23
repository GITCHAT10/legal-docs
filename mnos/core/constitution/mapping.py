"""
MNOS Sovereign Constitution - Global Mapping
Legal Root: MALDIVES INTERNATIONAL GROUP PVT LTD (UEI: 2024PV12395H)
"""

from typing import Dict

from mnos.shared.constants.root import ROOT_IDENTITY

CONSTITUTION: Dict[str, str] = {
    "LEGAL_ROOT": "MALDIVES INTERNATIONAL GROUP PVT LTD",
    "UEI": "2024PV12395H",
    "JURISDICTION": "MALDIVES",
    "DOCTRINE": "SOVEREIGN_CORE_V1.2_GENESIS_SEAL"
}

def get_legal_root() -> str:
    # Anchor to canonical constant
    return ROOT_IDENTITY
