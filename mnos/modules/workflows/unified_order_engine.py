import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
import hashlib
from pydantic import BaseModel, Field, field_validator

# Enforce Unified Order Primitive within MNOS Core
class OrderStatus(str):
    CREATED = "created"
    VALIDATED = "validated"
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_CONFIRMED = "payment_confirmed"
    EXECUTION_PENDING = "execution_pending"
    EXECUTION_CONFIRMED = "execution_confirmed"
    EXECUTION_FAILED = "execution_failed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class ModuleType(str):
    FOOD = "food"
    SHOP = "shop"
    RIDE = "ride"
    BOATS = "boats"
    WASH = "wash"
    EVENTS = "events"
    SERVICES = "services"
    TRAVEL = "travel"
    GIFT = "gift"

class AtollZone(str):
    MALE_CORE = "male_core"
    DIRECT_ATOLL = "direct_atoll"
    DEEP_ATOLL = "deep_atoll"

class UnifiedOrder(BaseModel):
    """Sovereign order primitive — all modules inherit this schema."""

    order_id: UUID = Field(default_factory=uuid4)
    aegis_id: str = Field(..., min_length=8)
    module: str
    island_code: str = Field(..., pattern=r"^[A-Z]{3}$")
    atoll_zone: str
    device_id: str

    subtotal_mvr: float = Field(..., ge=0)
    fee_breakdown: Dict[str, float] = Field(default_factory=dict)
    total_due_mvr: float = Field(..., ge=0)
    currency: str = "MVR"

    requires_physical_confirmation: bool = True
    confirmation_signals: List[str] = Field(default_factory=list)

    pdpa_consent_hash: str
    consent_purposes: List[str]

    shadow_audit_id: Optional[str] = None
    idempotency_key: str

    status: str = OrderStatus.CREATED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    module_payload: Dict[str, Any]

    @property
    def audit_hash(self) -> str:
        payload = f"{self.order_id}:{self.aegis_id}:{self.module}:{self.total_due_mvr}:{self.created_at.timestamp()}"
        return hashlib.sha256(payload.encode()).hexdigest()

def validate_primitive():
    print("--- 🏛️ UNIFIED ORDER ENGINE: PRIMITIVE VALIDATION ---")

    order = UnifiedOrder(
        aegis_id="aegis_guest_99",
        module=ModuleType.FOOD,
        island_code="GAN",
        atoll_zone=AtollZone.DEEP_ATOLL,
        device_id="device_customer_123",
        subtotal_mvr=250.0,
        fee_breakdown={"service_charge": 25.0, "tgst": 46.75},
        total_due_mvr=321.75,
        pdpa_consent_hash="sha256_abc",
        consent_purposes=["payment", "audit"],
        idempotency_key="idem_001",
        module_payload={"vendor_id": "V-123"}
    )

    print(f"Order ID: {order.order_id}")
    print(f"Audit Hash: {order.audit_hash}")
    assert order.status == OrderStatus.CREATED
    assert order.total_due_mvr == 321.75

    print("--- ✅ PRIMITIVE VALIDATION COMPLETE ---")

if __name__ == "__main__":
    validate_primitive()
