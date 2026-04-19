from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings

security = HTTPBearer()

async def verify_customs_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.scheme != "Bearer" or credentials.credentials != settings.CUSTOMS_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing customs token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials
