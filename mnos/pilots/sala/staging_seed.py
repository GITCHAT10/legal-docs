
SALA_PILOT_CONFIG = {
    "brand": "SALA",
    "jurisdiction": "MV",
    "business_unit": "RESORT_OPS",
    "tin": "SALA-MV-2026-STAGING"
}

def seed_staging():
    print(f"Seeding staging for {SALA_PILOT_CONFIG['brand']}...")
    return SALA_PILOT_CONFIG
