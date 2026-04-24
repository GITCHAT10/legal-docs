from fastapi import FastAPI
from mnos.shared.constants.root import ROOT_IDENTITY

app = FastAPI(title="BUILD-X DASHBOARD", description=f"CEO War Room for {ROOT_IDENTITY}")

@app.get("/health")
def health():
    return {"status": "ok", "interface": "buildx_dashboard"}

@app.get("/metrics/war-room")
def get_war_room_metrics():
    """
    BUILD-X DASHBOARD: 'Projected vs Actual vs Drift' for Water, Power, Revenue, and ESG.
    """
    return {
        "water": {"projected": 50000, "actual": 48500, "drift": -0.03},
        "power": {"projected": 450, "actual": 462, "drift": 0.027},
        "revenue": {"projected": 1200000, "actual": 1150000, "drift": -0.042},
        "esg": {"projected": 95, "actual": 94, "drift": -0.01}
    }

@app.post("/tasks/re-align")
def trigger_re_align(module: str, drift: float):
    """
    Trigger 'RE-ALIGN' task if AI forecast drift exceeds 15%.
    """
    if abs(drift) > 0.15:
        from mnos.core.events.service import events
        events.publish("OPTIMIZATION_APPLIED", {"module": module, "drift": drift, "action": "RE-ALIGN"})
        return {"status": "RE-ALIGN_TRIGGERED", "module": module, "drift": drift}

    return {"status": "STABLE", "module": module, "drift": drift}
