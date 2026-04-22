from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Event Contracts
EVENT_USER_VERIFIED = "USER_VERIFIED"
EVENT_VENDOR_APPROVED = "VENDOR_APPROVED"
EVENT_ORDER_CREATED = "ORDER_CREATED"
EVENT_PAYMENT_AUTHORIZED = "PAYMENT_AUTHORIZED"
EVENT_PAYMENT_CAPTURED = "PAYMENT_CAPTURED"
EVENT_DRIVER_ASSIGNED = "DRIVER_ASSIGNED"
EVENT_SHIPMENT_CREATED = "SHIPMENT_CREATED"
EVENT_SHIPMENT_DELIVERED = "SHIPMENT_DELIVERED"
EVENT_APPOINTMENT_BOOKED = "APPOINTMENT_BOOKED"
EVENT_CLASS_SCHEDULED = "CLASS_SCHEDULED"
EVENT_MEMBERSHIP_STARTED = "MEMBERSHIP_STARTED"
EVENT_AFFILIATE_CLICKED = "AFFILIATE_CLICKED"
EVENT_INSTALLMENT_CREATED = "INSTALLMENT_CREATED"
EVENT_PRAYER_REMINDER_TRIGGERED = "PRAYER_REMINDER_TRIGGERED"

class UserProfile(BaseModel):
    did: str
    name: str
    role: str # LOCAL_USER, WORK_PERMIT_USER, BUSINESS_VENDOR
    device_id: str

class OrderItem(BaseModel):
    item_id: str
    name: str
    price: float
    quantity: int
    carbon_footprint_kg: float = 0.0

class OrderRequest(BaseModel):
    user_id: str
    device_id: str
    vendor_id: str
    items: List[OrderItem]
    coupon_code: Optional[str] = None

class TransactionRecord(BaseModel):
    transaction_id: str
    user_id: str
    total_amount: float
    carbon_footprint_kg: float
    sala_compliant: bool = True
    timestamp: str
