from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import List, Dict, Any
from mnos.modules.air_grid.engine import AirGridEngine
import json
import asyncio

def create_air_grid_router(engine: AirGridEngine, get_actor_ctx):
    router = APIRouter(prefix="/air-grid", tags=["air-grid"])

    @router.post("/flight/ingest")
    async def ingest_flight(data: dict, actor: dict = Depends(get_actor_ctx)):
        return engine.ingest_flight_update(actor, data)

    @router.post("/transfer/assign/{flight_id}")
    async def assign_transfer(flight_id: str, actor: dict = Depends(get_actor_ctx)):
        return engine.assign_transfer(actor, flight_id)

    @router.post("/flight/land/{flight_id}")
    async def confirm_landing(flight_id: str, actor: dict = Depends(get_actor_ctx)):
        return engine.confirm_landing(actor, flight_id)

    @router.get("/flights")
    async def get_flights(actor: dict = Depends(get_actor_ctx)):
        return list(engine.flights.values())

    # Simulated WebSocket for Real-time Stream
    @router.websocket("/ws/dashboard")
    async def air_grid_ws(websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                # Stream current flight states every 5 seconds
                await websocket.send_json({
                    "type": "FLIGHT_SNAPSHOT",
                    "data": list(engine.flights.values())
                })
                await asyncio.sleep(5)
        except WebSocketDisconnect:
            pass

    return router
