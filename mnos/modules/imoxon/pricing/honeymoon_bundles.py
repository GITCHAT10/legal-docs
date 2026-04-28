from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

class RomanceTier(Enum):
    CLASSIC = "classic"          # Beach villa, 7N
    PREMIUM = "premium"          # Overwater villa, 7N
    LUXURY = "luxury"            # Overwater + experiences, 7N
    ULTIMATE = "ultimate"        # Multi-atoll, 10N, private yacht

@dataclass
class HoneymoonBundle:
    name: str
    nights: int
    accommodation_type: str
    romance_inclusions: List[str]  # e.g., ["sandbank_dinner", "couples_spa"]
    privacy_level: str  # "standard", "enhanced", "ultra_private"
    base_price_mvr: float
    commission_rate: float  # 0.28 to 0.40 for honeymoon niche
    upsell_modules: List[str]
    atoll_preferences: Optional[List[str]] = None  # e.g., ["Baa", "Noonu"] for UNESCO
    seasonal_multiplier: float = 1.0
    booking_window_months: int = 9  # Honeymoon: longer planning horizon

# Pre-configured bundles for EU honeymoon segment
HONEYMOON_BUNDLES = {
    "honeymoon_escape_7n": HoneymoonBundle(
        name="Maldives Honeymoon Escape (7N/6D)",
        nights=7,
        accommodation_type="overwater_villa",
        romance_inclusions=[
            "private_sandbank_dinner",
            "couples_spa_60min",
            "champagne_breakfast",
            "sunset_cruise",
            "professional_photo_session"
        ],
        privacy_level="enhanced",
        base_price_mvr=95000,
        commission_rate=0.28,
        upsell_modules=[
            "butler_upgrade",
            "private_yacht_day",
            "anniversary_rebooking_credit",
            "pre-arrival_romance_consultation"
        ],
        atoll_preferences=["North_Male", "South_Male", "Ari"],  # Easy transfers
        seasonal_multiplier=1.0,
        booking_window_months=9
    ),
    "honeymoon_luxury_7n": HoneymoonBundle(
        name="Maldives Luxury Honeymoon (7N/6D)",
        nights=7,
        accommodation_type="overwater_villa_premium",
        romance_inclusions=[
            "private_infinity_pool",
            "24hr_butler_service",
            "floating_breakfast_daily",
            "private_sandbank_dinner_with_photographer",
            "couples_spa_90min_with_ocean_view",
            "helicopter_transfer_upgrade_option"
        ],
        privacy_level="ultra_private",
        base_price_mvr=165000,
        commission_rate=0.32,
        upsell_modules=[
            "private_chef_experience",
            "underwater_restaurant_reservation",
            "seaplane_scenic_tour",
            "personalized_romance_ritual"
        ],
        atoll_preferences=["Baa", "Lhaviyani", "Noonu"],  # UNESCO biosphere resorts
        seasonal_multiplier=1.0,
        booking_window_months=12
    ),
    "honeymoon_ultimate_10n": HoneymoonBundle(
        name="Maldives Ultimate Honeymoon Expedition (10N/9D)",
        nights=10,
        accommodation_type="multi_resort_combination",
        romance_inclusions=[
            "2_resorts_experience",
            "private_yacht_day_with_crew",
            "multi_location_photo_story",
            "personalized_romance_scavenger_hunt",
            "anniversary_rebooking_guarantee",
            "dedicated_romance_coordinator_24_7"
        ],
        privacy_level="ultra_private",
        base_price_mvr=245000,
        commission_rate=0.40,
        upsell_modules=[
            "private_island_buyout_option",
            "vow_renewal_ceremony",
            "custom_romance_film_production",
            "lifetime_anniversary_benefits"
        ],
        atoll_preferences=["Remote_Atolls"],  # Requires special permits, ultra-exclusive
        seasonal_multiplier=1.0,
        booking_window_months=12
    )
}
