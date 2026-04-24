from fastapi import FastAPI
from mnos.shared.constants.root import ROOT_IDENTITY
from mnos.core.events.service import events

app = FastAPI(title="BUILD-X ARCH", description=f"AI Resort Design Engine for {ROOT_IDENTITY}")

@app.get("/health")
def health():
    return {"status": "ok", "module": "buildx_arch"}

@app.post("/design/generate")
def generate_design(specs: dict):
    """
    BUILD-X ARCH: AI Resort Design Engine.
    Generates layout and utility demand models.
    """
    design_data = {
        "project_id": specs.get("project_id", "PRJ-TEMP"),
        "layout": "BLOCK_BASED_V1",
        "utility_demand": {
            "water_liters_per_day": 50000,
            "power_kw_peak": 450
        }
    }

    events.publish("DESIGN_CREATED", design_data)

    return design_data
