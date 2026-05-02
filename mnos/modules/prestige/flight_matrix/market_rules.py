from typing import Dict, Any

MARKET_RULES = {
    "EU": {
        "drivers": ["sustainability", "diving", "barefoot luxury", "all-inclusive value"],
        "default_privacy": 2
    },
    "CIS": {
        "drivers": ["ultra-luxury", "prestige brands", "large villas", "privacy"],
        "default_privacy": 3
    },
    "GCC": {
        "drivers": ["privacy", "family villas", "Halal-friendly dining", "VIP/CIP"],
        "default_privacy": 3
    },
    "Asia": {
        "drivers": ["design", "wellness", "culinary variety", "photo-centric travel"],
        "default_privacy": 2
    },
    "Global UHNW": {
        "drivers": ["ultra-exclusive", "personalized service", "security", "jet_access"],
        "default_privacy": 4
    }
}

def get_market_profile(market_region: str) -> Dict[str, Any]:
    return MARKET_RULES.get(market_region, {"drivers": [], "default_privacy": 2})
