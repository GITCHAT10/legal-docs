from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
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

class ClearancePrecheckSchema(BaseModel):
    shipment_id: str
    items: List[Dict]
    total_cif_value_mvr: float
    importer_registration: str

class GoodsDeclarationSchema(BaseModel):
    shipment_id: str
    declaration_type: str
    documents: Dict[str, str]

class DutyPaymentSchema(BaseModel):
    declaration_id: str
    amount_mvr: float
    payment_source: str
    breakdown: Dict[str, float]

class ReleaseMarkSchema(BaseModel):
    declaration_id: str
    evidence: Dict[str, Any]

class GateOutSchema(BaseModel):
    declaration_id: str
    mpl_gate_pass: str
    vehicle_details: Dict[str, str]
