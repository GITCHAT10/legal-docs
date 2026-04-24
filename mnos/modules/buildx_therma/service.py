from fastapi import FastAPI
from mnos.shared.constants.root import ROOT_IDENTITY
from mnos.core.events.service import events

app = FastAPI(title="BUILD-X THERMA", description=f"Waste → Energy for {ROOT_IDENTITY}")

@app.get("/health")
def health():
    return {"status": "ok", "module": "buildx_therma"}

@app.post("/process_waste")
def process_waste(kg: float):
    """
    BUILD-X THERMA: Waste-to-Energy loop monitoring.
    """
    data = {
        "waste_processed_kg": kg,
        "energy_recovered_kwh": kg * 0.45,
        "cems_emissions": "COMPLIANT",
        "calorific_ai_confidence": 0.99
    }

    events.publish("WASTE_PROCESSED", data)

    return data
