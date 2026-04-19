from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid

app = FastAPI(title="MNOS INVENTORY")

class StockUpdate(BaseModel):
    item_id: str
    quantity: int

@app.post("/api/inventory/update")
async def update_stock(update: StockUpdate):
    return {"status": "success", "updated_item": update.item_id}

@app.get("/health")
async def health():
    return {"status": "ok"}
