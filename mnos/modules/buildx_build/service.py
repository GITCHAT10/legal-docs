from fastapi import FastAPI
from mnos.shared.constants.root import ROOT_IDENTITY
from mnos.core.events.service import events

app = FastAPI(title="BUILD-X BUILD", description=f"Construction & BOQ for {ROOT_IDENTITY}")

@app.get("/health")
def health():
    return {"status": "ok", "module": "buildx_build"}

@app.post("/boq/calculate")
def calculate_boq(beds: int):
    """
    BUILD-X BUILD: Construction & BOQ Engine.
    Enforces Maldives MOT 1:1.5 staff-to-bed ratios.
    """
    staff_count = int(beds * 1.5)
    boq = {
        "beds": beds,
        "staff_required": staff_count,
        "total_cost_mvr": beds * 250000,
        "items": [
            {"item": "Modular Room Unit", "quantity": beds},
            {"item": "Staff Quarter Unit", "quantity": staff_count // 2}
        ]
    }

    events.publish("BOQ_GENERATED", boq)

    return boq
