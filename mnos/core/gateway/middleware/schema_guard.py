from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from mnos.core.events.validator import validate_event
import json

class SchemaGuard(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        if request.method == "POST" and request.url.path.endswith("/events/publish"):
            try:
                body = await request.body()
                if not body:
                    return JSONResponse(status_code=400, content={"detail": "Empty request body"})

                event = json.loads(body)
                valid, msg = validate_event(event)
                if not valid:
                    # Invalid events must fail closed
                    return JSONResponse(status_code=400, content={"detail": f"SCHEMA_GUARD_REJECTION: {msg}"})
            except json.JSONDecodeError:
                return JSONResponse(status_code=400, content={"detail": "Invalid JSON"})
            except Exception as e:
                return JSONResponse(status_code=500, content={"detail": str(e)})

        response = await call_next(request)
        return response
