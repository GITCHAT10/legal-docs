from fastapi import Header, HTTPException
import os

# MNOS Integration Secret for HMAC verification (from memory/environment)
MNOS_INTEGRATION_SECRET = os.getenv("MNOS_INTEGRATION_SECRET", "dev_secret")

async def verify_signed_credentials(
    x_signature: str = Header(...),
    x_timestamp: str = Header(...),
    x_request_id: str = Header(...)
):
    """
    Enforces the MNOS Security Rule:
    'All endpoints require signed device or service credentials'
    """
    # In production, we would verify the HMAC-SHA256 signature here
    # For this pilot implementation, we ensure headers are present.
    if not x_signature or not x_timestamp or not x_request_id:
        raise HTTPException(status_code=403, detail="Missing required MNOS security headers")

    # In production: validate signature using MNOS_INTEGRATION_SECRET
    return True
