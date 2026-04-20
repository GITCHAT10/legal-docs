from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class AttendanceScan(Base):
    __tablename__ = "attendance_scans"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    ticket_id = Column(String, nullable=False, index=True)
    event_id = Column(String, nullable=False, index=True)
    scanner_aegis_id = Column(String, index=True)
    device_id = Column(String)
    scan_mode = Column(String)
    scan_result = Column(String)
    scanned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    offline_batch_id = Column(String, index=True)
    trace_id = Column(String)

class OfflineSyncBatch(Base):
    __tablename__ = "offline_sync_batches"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    device_id = Column(String, nullable=False, index=True)
    batch_status = Column(String, default="PENDING")
    payload_hash = Column(String)
    received_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    committed_at = Column(DateTime)

class EdgeSyncConflict(Base):
    __tablename__ = "edge_sync_conflicts"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    resource_type = Column(String)
    resource_id = Column(String)
    device_id = Column(String)
    conflict_type = Column(String)
    resolution_status = Column(String, default="UNRESOLVED")
    trace_id = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
