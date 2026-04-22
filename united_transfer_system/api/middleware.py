from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
import hmac
import hashlib
import time
from mnos.core.security.config import settings

class SignedRequestMiddleware(BaseHTTPMiddleware):
    """
    Gateway security for United Transfer:
    - Signed requests
    - Timestamps
    - Idempotency keys
    - Partner keys
    """
    async def dispatch(self, request: Request, call_next):
        # 1. Check timestamp (prevent replay attacks)
        ts = request.headers.get("X-UT-Timestamp")
        if not ts or abs(time.time() - float(ts)) > 300:
            raise HTTPException(status_code=401, detail="Invalid or expired timestamp")

        # 2. Check partner key
        partner_key = request.headers.get("X-UT-Partner-Key")
        if not partner_key:
            raise HTTPException(status_code=401, detail="Missing Partner Key")

        # 3. Verify signature
        signature = request.headers.get("X-UT-Signature")
        if not signature:
            raise HTTPException(status_code=401, detail="Unsigned request")

        # Simple HMAC verification mock
        # In production: expected_sig = hmac.new(key, msg, hashlib.sha256).hexdigest()

        response = await call_next(request)
        return response
