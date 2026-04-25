from sqlalchemy import Column, String, Float, JSON, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from mnos.db.schema import Base
from sqlalchemy.sql import func
import uuid

class LogisticsShipment(Base):
    __tablename__ = 'logistics_shipments'
    id = Column(String(50), primary_key=True)
    supplier_id = Column(String(50), nullable=False)
    order_id = Column(String(50))
    origin = Column(String(100))
    destination = Column(String(100))
    status = Column(String(30), default='CREATED') # DISPATCHED, ARRIVED, CLEARED, RECEIVED
    created_at = Column(DateTime, server_default=func.now())

class LogisticsShipmentItem(Base):
    __tablename__ = 'logistics_shipment_items'
    id = Column(String(50), primary_key=True)
    shipment_id = Column(String(50), ForeignKey('logistics_shipments.id'))
    sku = Column(String(50))
    name = Column(String(150))
    quantity = Column(Float)
    unit_price = Column(Float)

class PortClearanceJob(Base):
    __tablename__ = 'port_clearance_jobs'
    id = Column(String(50), primary_key=True)
    shipment_id = Column(String(50), ForeignKey('logistics_shipments.id'))
    agent_id = Column(String(50))
    status = Column(String(30), default='PENDING') # STARTED, RELEASED
    cleared_at = Column(DateTime)

class SkygodownReceipt(Base):
    __tablename__ = 'skygodown_receipts'
    id = Column(String(50), primary_key=True)
    shipment_id = Column(String(50), ForeignKey('logistics_shipments.id'))
    operator_id = Column(String(50))
    received_at = Column(DateTime, server_default=func.now())

class SkygodownLot(Base):
    __tablename__ = 'skygodown_lots'
    id = Column(String(50), primary_key=True)
    receipt_id = Column(String(50), ForeignKey('skygodown_receipts.id'))
    sku = Column(String(50))
    total_quantity = Column(Float)
    available_quantity = Column(Float)

class LotAllocation(Base):
    __tablename__ = 'lot_allocations'
    id = Column(String(50), primary_key=True)
    lot_id = Column(String(50), ForeignKey('skygodown_lots.id'))
    buyer_id = Column(String(50))
    resort_id = Column(String(50))
    allocated_quantity = Column(Float)
    status = Column(String(30), default='ALLOCATED') # MANIFESTED, DELIVERED

class DeliveryManifest(Base):
    __tablename__ = 'delivery_manifests'
    id = Column(String(50), primary_key=True)
    destination_id = Column(String(50))
    captain_id = Column(String(50))
    vessel_id = Column(String(50))
    status = Column(String(30), default='CREATED') # DISPATCHED, DELIVERED
    created_at = Column(DateTime, server_default=func.now())

class ManifestItem(Base):
    __tablename__ = 'manifest_items'
    id = Column(String(50), primary_key=True)
    manifest_id = Column(String(50), ForeignKey('delivery_manifests.id'))
    allocation_id = Column(String(50), ForeignKey('lot_allocations.id'))
    sku = Column(String(50))
    quantity = Column(Float)

class TransportAssignment(Base):
    __tablename__ = 'transport_assignments'
    id = Column(String(50), primary_key=True)
    manifest_id = Column(String(50), ForeignKey('delivery_manifests.id'))
    driver_id = Column(String(50))
    device_id = Column(String(50))
    assigned_at = Column(DateTime, server_default=func.now())

class DeliveryScanEvent(Base):
    __tablename__ = 'delivery_scan_events'
    id = Column(String(50), primary_key=True)
    manifest_id = Column(String(50), ForeignKey('delivery_manifests.id'))
    actor_id = Column(String(50))
    scan_type = Column(String(20)) # LOAD, UNLOAD
    timestamp = Column(DateTime, server_default=func.now())
    is_offline = Column(Boolean, default=False)

class DeliveryReceipt(Base):
    __tablename__ = 'delivery_receipts'
    id = Column(String(50), primary_key=True)
    manifest_id = Column(String(50), ForeignKey('delivery_manifests.id'))
    recipient_id = Column(String(50))
    received_items = Column(JSON)
    status = Column(String(30)) # CONFIRMED, DISPUTED
    confirmed_at = Column(DateTime, server_default=func.now())

class DeliveryVariance(Base):
    __tablename__ = 'delivery_variances'
    id = Column(String(50), primary_key=True)
    receipt_id = Column(String(50), ForeignKey('delivery_receipts.id'))
    sku = Column(String(50))
    expected_qty = Column(Float)
    actual_qty = Column(Float)
    variance_pct = Column(Float)
    notes = Column(Text)

class LogisticsAuditEvent(Base):
    __tablename__ = 'logistics_audit_events'
    id = Column(String(50), primary_key=True)
    entity_id = Column(String(50))
    entity_type = Column(String(50))
    action = Column(String(50))
    actor_id = Column(String(50))
    trace_id = Column(String(50))
    payload = Column(JSON)
    timestamp = Column(DateTime, server_default=func.now())
