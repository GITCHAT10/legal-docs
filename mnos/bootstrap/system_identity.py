def ensure_system_identity(identity_core, shadow_core):
    """
    Idempotent bootstrap of the MNOS SYSTEM identity and device binding.
    """
    if "SYSTEM" not in identity_core.profiles:
        identity_core.profiles["SYSTEM"] = {
            "identity_id": "SYSTEM",
            "profile_type": "admin",
            "full_name": "MNOS SYSTEM",
            "verification_status": "verified",
            "persistent_identity_hash": "SYSTEM-HASH"
        }

    if "SYSTEM-DEVICE" not in identity_core.devices:
        identity_core.devices["SYSTEM-DEVICE"] = {
            "device_id": "SYSTEM-DEVICE",
            "identity_id": "SYSTEM",
            "trust_level": "high"
        }

    # Forensic record of bootstrap if not already present in chain
    if not any(b.get("event_type") == "system.bootstrap" for b in shadow_core.chain):
        shadow_core.commit("system.bootstrap", "SYSTEM", {"status": "READY"})
