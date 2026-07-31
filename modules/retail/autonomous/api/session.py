from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..models.schemas import SessionStartRequest, SessionResponse
from ..models.database import RetailSession, get_db
from ..services.adapters import AEGISAdapter, EVENTSAdapter, SHADOWAdapter
from ..services.security import verify_signed_credentials
from ..events.contracts import EVENT_SESSION_STARTED
import uuid
from datetime import datetime, timezone

router = APIRouter(dependencies=[Depends(verify_signed_credentials)])

@router.post("/session/start", response_model=SessionResponse)
async def start_session(request: SessionStartRequest, db: Session = Depends(get_db)):
    aegis = AEGISAdapter()
    events = EVENTSAdapter()
    shadow = SHADOWAdapter()

    # 1. Call MNOS AEGIS service
    auth_result = await aegis.validate_token(request.auth_token)
    if not auth_result.get("valid"):
        raise HTTPException(status_code=401, detail="Invalid AEGIS token or unauthorized")

    # 2. Verify user and wallet/folio eligibility (Simplified for this mock)
    aegis_user_id = uuid.UUID(auth_result["aegis_user_id"])
    tenant_id = uuid.UUID(auth_result["tenant_id"])

    # 3. Create retail session
    session_id = uuid.uuid4()
    trace_id = uuid.uuid4()

    new_session = RetailSession(
        id=session_id,
        tenant_id=tenant_id,
        aegis_user_id=aegis_user_id,
        store_id=request.store_id,
        auth_type=request.auth_type,
        trace_id=trace_id,
        status="OPEN"
    )
    db.add(new_session)
    db.commit()

    # 4. Emit EVENTS.retail.session_started
    await events.publish(EVENT_SESSION_STARTED, {
        "session_id": str(session_id),
        "tenant_id": str(tenant_id),
        "aegis_user_id": str(aegis_user_id),
        "store_id": request.store_id,
        "trace_id": str(trace_id)
    })

    # 5. Commit SHADOW entry
    await shadow.commit({
        "tenant_id": str(tenant_id),
        "trace_id": str(trace_id),
        "entity_type": "A_RETAIL_SESSION",
        "entity_id": str(session_id),
        "event_type": "SESSION_STARTED",
        "payload": {
            "aegis_user_id": str(aegis_user_id),
            "store_id": request.store_id,
            "auth_type": request.auth_type
        }
    })

    # 6. Return unlock=true only if validation passes
    return SessionResponse(
        session_id=session_id,
        status="OPEN",
        unlock=True
    )
