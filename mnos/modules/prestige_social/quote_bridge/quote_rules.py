# Maldives 2026 Pricing Constants
SERVICE_CHARGE_RATE = 0.10
TGST_RATE = 0.17

# Green Tax Rates (USD per guest per day)
GREEN_TAX_RESORT = 12.0
GREEN_TAX_SMALL_GUESTHOUSE = 6.0

# Mock Resort Data for MVP Staging
MOCK_RESORTS = {
    "RITZ_CARLTON_MALDIVES": {
        "name": "The Ritz-Carlton Maldives, Fari Islands",
        "room_category": "overwater_villa",
        "base_contract_rate": 7800.0,
        "transfer_mode": "speedboat",
        "transfer_fee": 650.0,
        "accommodation_type": "resort",
        "green_tax_rate": GREEN_TAX_RESORT
    },
    "SONEVA_JANI": {
        "name": "Soneva Jani",
        "room_category": "overwater_villa",
        "base_contract_rate": 9500.0,
        "transfer_mode": "seaplane",
        "transfer_fee": 950.0,
        "accommodation_type": "resort",
        "green_tax_rate": GREEN_TAX_RESORT
    },
    "FAMILY_GUESTHOUSE_SMALL": {
        "name": "Family Guesthouse Small",
        "room_category": "family_room",
        "base_contract_rate": 1200.0,
        "transfer_mode": "speedboat",
        "transfer_fee": 180.0,
        "accommodation_type": "inhabited_island_guesthouse",
        "room_count": 30,
        "green_tax_rate": GREEN_TAX_SMALL_GUESTHOUSE
    },
    "LUXURY_RESORT_PRIVATE_POOL": {
        "name": "Luxury Resort Private Pool",
        "room_category": "beach_pool_villa",
        "base_contract_rate": 6200.0,
        "transfer_mode": "speedboat",
        "transfer_fee": 500.0,
        "accommodation_type": "resort",
        "green_tax_rate": GREEN_TAX_RESORT
    }
}
