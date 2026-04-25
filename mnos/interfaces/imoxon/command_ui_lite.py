def get_command_ui_metadata():
    return {
        "views": [
            "identity_binding_dashboard",
            "unverified_actor_alerts",
            "delivery_acceptance_board",
            "asset_binding_registry"
        ],
        "widgets": [
            {"id": "verified_staff_counter", "label": "Verified Staff", "source": "aegis.registry.verified"},
            {"id": "device_binding_status", "label": "Device Trust", "source": "aegis.device.trust"},
            {"id": "pending_verification_queue", "label": "Pending KYB", "source": "aegis.identity.pending"}
        ],
        "principles": {
            "one_primary_identity_alert_only": True,
            "show_actor_location_on_sensitive_actions": True
        }
    }
