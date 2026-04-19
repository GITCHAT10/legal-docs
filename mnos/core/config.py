import os
import logging

def get_mnos_config():
    secret = os.getenv("MNOS_INTEGRATION_SECRET")
    insecure_dev = os.getenv("ALLOW_INSECURE_DEV", "false").lower() == "true"

    if not secret:
        if insecure_dev:
            logging.warning("MNOS_INTEGRATION_SECRET missing - INSECURE DEV MODE ENABLED")
        else:
            raise RuntimeError("MNOS_INTEGRATION_SECRET NOT CONFIGURED - SYSTEM HALT. Use ALLOW_INSECURE_DEV=true for development.")

    return {
        "MNOS_INTEGRATION_SECRET": secret,
        "mode": "insecure_dev" if not secret and insecure_dev else "enforced"
    }

config = get_mnos_config()
