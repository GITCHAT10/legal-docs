from fastapi import FastAPI
from mnos.shared.constants.root import ROOT_IDENTITY
from mnos.core.events.service import events

app = FastAPI(title="BUILD-X LOG", description=f"Logistics (UT) for {ROOT_IDENTITY}")

@app.get("/health")
def health():
    return {"status": "ok", "module": "buildx_log"}

@app.post("/transfer/schedule")
def schedule_transfer(data: dict):
    """
    BUILD-X LOG: Logistics & Traceability.
    Connects design, build, and operations.
    """
    transfer_info = {
        "transfer_id": data.get("transfer_id", "TR-001"),
        "status": "SCHEDULED",
        "trace_id": data.get("trace_id")
    }

    events.publish("TURNAROUND_COMPLETED", transfer_info)

    return transfer_info
