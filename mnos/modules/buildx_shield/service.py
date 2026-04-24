from fastapi import FastAPI, Header, HTTPException
from mnos.shared.constants.root import ROOT_IDENTITY
import json
from mnos.core.security.aegis import aegis

app = FastAPI(title="BUILD-X SHIELD", description=f"AEGIS Identity Governance for {ROOT_IDENTITY}")

@app.get("/health")
def health():
    return {"status": "ok", "module": "buildx_shield"}

@app.get("/governance/check")
def check_governance(x_aegis_signature: str = Header(...), session_context: str = Header(...)):
    """
    BUILD-X SHIELD: Identity-bound access governance.
    Connects to core AEGIS for device and identity verification.
    """
    try:
        context = json.loads(session_context)
        context["signature"] = x_aegis_signature
        aegis.validate_session(context)
        return {"status": "AUTHORIZED", "identity": context["user_id"]}
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))
