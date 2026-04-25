from fastapi import APIRouter, Depends, HTTPException, Path
from typing import List
from .schemas import (
    ShipmentCreateSchema, PortClearanceSchema, ReceiptSchema,
    LotRegistrationSchema, AllocationCreateSchema, ManifestCreateSchema,
    TransportAssignSchema, ScanEventSchema, ReceiptConfirmSchema,
    SettlementReleaseSchema, VarianceReportSchema
)

def create_logistics_router(engine, get_actor_ctx):
    router = APIRouter(prefix="/api/v1/logistics", tags=["logistics"])

    @router.post("/shipment/create")
    async def create_shipment(data: ShipmentCreateSchema, actor: dict = Depends(get_actor_ctx)):
        return engine.create_shipment(actor, data.model_dump())

    @router.post("/shipment/{id}/dispatch")
    async def dispatch_shipment(id: str = Path(...), actor: dict = Depends(get_actor_ctx)):
        return engine.dispatch_shipment(actor, id)

    @router.post("/port/arrival")
    async def port_arrival(shipment_id: str, actor: dict = Depends(get_actor_ctx)):
        return engine.record_port_arrival(actor, shipment_id)

    @router.post("/port/{id}/clearance")
    async def port_clearance(id: str = Path(...), data: PortClearanceSchema = None, actor: dict = Depends(get_actor_ctx)):
        agent_id = data.agent_id if data else "SYSTEM_AGENT"
        return engine.clear_port(actor, id, agent_id)

    @router.post("/skygodown/receive")
    async def skygodown_receive(shipment_id: str, operator_id: str, actor: dict = Depends(get_actor_ctx)):
        return engine.receive_at_skygodown(actor, shipment_id, operator_id)

    @router.post("/lots/register")
    async def register_lot(data: LotRegistrationSchema, actor: dict = Depends(get_actor_ctx)):
        return engine.register_lot(actor, data.receipt_id, data.sku, data.quantity)

    @router.post("/allocations/create")
    async def create_allocation(data: AllocationCreateSchema, actor: dict = Depends(get_actor_ctx)):
        return engine.create_allocation(actor, data.lot_id, data.buyer_id, data.resort_id, data.quantity)

    @router.post("/manifest/create")
    async def create_manifest(data: ManifestCreateSchema, actor: dict = Depends(get_actor_ctx)):
        return engine.create_manifest(actor, data.model_dump())

    @router.post("/transport/assign")
    async def assign_transport(data: TransportAssignSchema, manifest_id: str, actor: dict = Depends(get_actor_ctx)):
        return engine.assign_transport(actor, manifest_id, data.driver_id, data.device_id)

    @router.post("/scan/load")
    async def scan_load(data: ScanEventSchema, actor: dict = Depends(get_actor_ctx)):
        return engine.confirm_scan(actor, data.manifest_id, "LOAD", data.is_offline)

    @router.post("/scan/unload")
    async def scan_unload(data: ScanEventSchema, actor: dict = Depends(get_actor_ctx)):
        return engine.confirm_scan(actor, data.manifest_id, "UNLOAD", data.is_offline)

    @router.post("/receipt/confirm")
    async def confirm_receipt(manifest_id: str, data: ReceiptConfirmSchema, actor: dict = Depends(get_actor_ctx)):
        return engine.confirm_delivery_receipt(actor, manifest_id, data.recipient_id, data.received_items)

    @router.post("/variance/report")
    async def report_variance(receipt_id: str, data: VarianceReportSchema, actor: dict = Depends(get_actor_ctx)):
        return engine.report_variance(actor, receipt_id, data.model_dump())

    @router.post("/settlement/release")
    async def settlement_release(data: SettlementReleaseSchema, actor: dict = Depends(get_actor_ctx)):
        return engine.release_settlement(actor, data.manifest_id, data.order_id)

    @router.get("/track/{shipment_id}")
    async def track_shipment(shipment_id: str):
        if shipment_id not in engine.shipments:
             raise HTTPException(status_code=404, detail="Shipment not found")
        return engine.shipments[shipment_id]

    @router.get("/manifest/{manifest_id}")
    async def get_manifest(manifest_id: str):
        if manifest_id not in engine.manifests:
             raise HTTPException(status_code=404, detail="Manifest not found")
        return engine.manifests[manifest_id]

    @router.get("/audit/{trace_id}")
    async def get_audit_trail(trace_id: str):
        # In a real system we would query the database or shadow store
        # For prototype, we return the SHADOW chain filtered by trace_id if possible
        # Or just a placeholder for now
        return {"trace_id": trace_id, "events": []}

    return router
