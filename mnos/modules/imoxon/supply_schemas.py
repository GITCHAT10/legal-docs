from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Event Contracts
EVENT_DEMAND_SIGNAL_VALIDATED = "DEMAND_SIGNAL_VALIDATED"
EVENT_DEMAND_BATCH_LOCKED = "DEMAND_BATCH_LOCKED"
EVENT_RFP_OPENED = "RFP_OPENED"
EVENT_BID_SUBMITTED = "BID_SUBMITTED"
EVENT_SUPPLIER_AWARDED = "SUPPLIER_AWARDED"
EVENT_SHIPMENT_DISPATCHED = "SHIPMENT_DISPATCHED"
EVENT_SKYGODOWN_RECEIVED = "SKYGODOWN_RECEIVED"
EVENT_LOT_ALLOCATED = "LOT_ALLOCATED"
EVENT_MANIFEST_CREATED = "MANIFEST_CREATED"
EVENT_RESORT_RECEIPT_ACCEPTED = "RESORT_RECEIPT_ACCEPTED"

class DemandSignal(BaseModel):
    id: str
    resort_id: str
    items: List[Dict[str, Any]]
    urgency: str # NORMAL, EMERGENCY
    timestamp: str

class ProcurementRFP(BaseModel):
    id: str
    batch_id: str
    items: List[Dict[str, Any]]
    recipients: List[str]
    status: str # OPEN, AWARDED, CLOSED

class SkygodownLot(BaseModel):
    id: str
    rfp_id: str
    supplier_id: str
    received_at: str
    items: List[Dict[str, Any]]
    qc_passed: bool = False

class DeliveryManifest(BaseModel):
    id: str
    lot_ids: List[str]
    captain_id: str
    destination_resort_id: str
    status: str # PENDING, IN_TRANSIT, DELIVERED
