import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from mnos.core.db.base_class import Base
from mnos.core.db.sync_buffer import sync_buffer
from mnos.modules.shadow.models import Evidence

# Mock DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_sync.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_offline_sync_flow():
    """Demonstrate Phase 3: Offline transaction -> sync -> SHADOW commit."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # 1. Offline Phase: No SHADOW access, but buffered locally
    sync_buffer.queue_transaction("OFFLINE-001", {"sale": 500, "item": "Room Service"})
    sync_buffer.queue_transaction("OFFLINE-002", {"sale": 100, "item": "Laundry"})

    # 2. Sync Phase: Reconnect and seal
    sealed = sync_buffer.process_sync(db)
    assert len(sealed) == 2

    # 3. Verification: SHADOW ledger holds the records
    ev1 = db.query(Evidence).filter(Evidence.trace_id == "OFFLINE-001").first()
    assert ev1 is not None
    assert ev1.action == "OFFLINE_SYNC"

    Base.metadata.drop_all(bind=engine)
