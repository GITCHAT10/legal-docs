from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class ShipmentItemSchema(BaseModel):
    sku: str
    name: str
    quantity: float
    unit_price: float

class ShipmentCreateSchema(BaseModel):
    supplier_id: str
    order_id: Optional[str] = None
    origin: str
    destination: str
    items: List[ShipmentItemSchema]

class PortClearanceSchema(BaseModel):
    agent_id: str

class ReceiptSchema(BaseModel):
    operator_id: str

class LotRegistrationSchema(BaseModel):
    receipt_id: str
    sku: str
    quantity: float

class AllocationCreateSchema(BaseModel):
    lot_id: str
    buyer_id: str
    resort_id: str
    quantity: float

class ManifestCreateSchema(BaseModel):
    destination_id: str
    captain_id: str
    vessel_id: str
    allocation_ids: List[str]

class TransportAssignSchema(BaseModel):
    driver_id: str
    device_id: str

class ScanEventSchema(BaseModel):
    manifest_id: str
    scan_type: str # LOAD, UNLOAD
    is_offline: bool = False
    qr_payload: Optional[str] = None

class ReceiptConfirmSchema(BaseModel):
    recipient_id: str
    received_items: List[Dict] # {sku, qty}

class VarianceReportSchema(BaseModel):
    sku: str
    expected_qty: float
    actual_qty: float
    notes: Optional[str] = None

class SettlementReleaseSchema(BaseModel):
    manifest_id: str
    order_id: str
