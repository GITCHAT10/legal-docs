from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import os

from mnos.core.eleone import eleone
from mnos.modules.shadow.service import shadow
from mnos.modules.events.engine import event_engine
from mnos.modules.aegis.verifier import aegis
from mnos.modules.moats.engine import moats
from mnos.modules.infra.sewer import sewer_engine
from mnos.modules.layout.generator import sie
from mnos.modules.compliance.checker import compliance
from mnos.modules.finance.boq import boq_engine
from mnos.modules.gis.engine import gis_engine
from mnos.modules.aquasync.engine import aquasync

app = FastAPI(title="MNOS NextGen ASI - Maldives")

# Serve static files for the frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

class DesignRequest(BaseModel):
    plot_width: float
    plot_depth: float
    target_rooms: int
    island_name: str

@app.get("/health")
def health():
    return {"status": "ONLINE", "version": "1.0.0-skyi-core"}

@app.post("/api/v1/design")
async def generate_design(req: DesignRequest, request: Request):
    # Security check (simplified)
    # token = request.headers.get("X-NEXGEN-TOKEN")
    # if not token or not aegis.verify_token(token, "admin"):
    #     raise HTTPException(status_code=403, detail="Forbidden")

    # GIS Pre-check
    island_info = gis_engine.get_island_data(req.island_name)
    if "error" in island_info:
        raise HTTPException(status_code=400, detail="Invalid island name")

    # Geometry Generation (SIE)
    try:
        layout = sie.generate_layout(req.plot_width, req.plot_depth, req.target_rooms)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Compliance Check (AEGIS)
    total_area = req.plot_width * req.plot_depth * 2 # assumed 2 floors
    comp = compliance.verify_compliance(total_area, req.plot_width * req.plot_depth, 2, layout["rooms_per_floor"])

    # BOQ Generation (FCE + MOATS)
    boq = boq_engine.generate_boq(layout, 2)

    # Event Emission
    await event_engine.emit("nexus.design.created", {"island": req.island_name, "rooms": req.target_rooms})

    # Shadow Audit
    shadow.commit("req_001", "DESIGN_GEN", {"input": req.dict(), "output": layout})

    # Eleone Decision Log
    eleone.log_decision("DESIGN_GENERATION", req.dict(), layout)

    return {
        "island": island_info,
        "layout": layout,
        "compliance": comp,
        "boq": boq
    }

@app.get("/api/v1/gis/islands")
def list_islands():
    return gis_engine.islands

@app.get("/api/v1/aquasync/simulate")
def simulate_aquasync(tier: str = "Bronze"):
    return aquasync.run_simulation(tier, 35000) # Seawater salinity ppm

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
