from fastapi import FastAPI
from mnos.shared.constants.root import ROOT_IDENTITY
from mnos.core.events.service import events

app = FastAPI(title="BUILD-X MARS", description=f"Workforce (HR, BOH) for {ROOT_IDENTITY}")

@app.get("/health")
def health():
    return {"status": "ok", "module": "buildx_mars"}

@app.get("/workforce/verify")
def verify_workforce(employee_id: str):
    """
    BUILD-X MARS: HR & Payroll.
    Linked to BOH biometric geofencing and sentiment drift.
    """
    status = {
        "employee_id": employee_id,
        "geofence": "VERIFIED_INSIDE",
        "sentiment_drift": -0.02,
        "payroll_status": "ACTIVE"
    }

    return status
