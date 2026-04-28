NEW_TRIGGER_SEGMENTS = {
    "us_luxury": {
        "template": "luxury_experience_bundle",
        "priority": "A",
        "volume_daily": 15,
        "expected_cvr": 0.08,
        "avg_booking_value": 4500
    },
    "latam_honeymoon": {
        "template": "romance_package_bundle",
        "priority": "A/B",
        "volume_daily": 20,
        "expected_cvr": 0.10,
        "avg_booking_value": 2800
    },
    "asia_fast": {
        "template": "quick_quote_package",
        "priority": "A/B",
        "volume_daily": 25,
        "expected_cvr": 0.12,
        "avg_booking_value": 2200
    },
    "eu_luxury": {
        "template": "luxury_experience_bundle",
        "priority": "A",
        "volume_daily": 15,
        "expected_cvr": 0.10,
        "avg_booking_value": 3200
    }
}

SIGNAL_WEIGHTS_EU = {
    "pdf_view": 0.25,
    "weekend_open": 0.15,
    "past_lead_quality": 0.20,
    "click_count_15m": 0.08,
    "reply_count_24h": 0.18,
    "bookings_90d": 0.12,
    "session_duration_45s": 0.05
}

THRESHOLDS_EU = {
    "intercept_now": 0.80,
    "priority_offer": 0.60,
    "nurture": 0.35
}
