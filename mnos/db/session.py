from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os

# Production DB config via ENV
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://imoxon:secure@localhost:5432/imoxon_prod")

# For prototype/audit, use SQLite if Postgres not provided
if "sqlite" in DATABASE_URL or not os.environ.get("DATABASE_URL"):
    DATABASE_URL = "sqlite:///./imoxon_prod.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from mnos.db.schema import Base
    # Ensure all models are imported so metadata is populated
    from mnos.modules.imoxon.schemas.models import ImoxonSupplier, ImoxonCatalogProduct, ImoxonOrder, ImoxonWarehouseStock
    from mnos.modules.imoxon.logistics.models import LogisticsShipment, LogisticsShipmentItem, PortClearanceJob, SkygodownReceipt, SkygodownLot, LotAllocation, DeliveryManifest, ManifestItem, TransportAssignment, DeliveryScanEvent, DeliveryReceipt, DeliveryVariance, ClearanceDeclaration, PCAVault, TariffEntry, LogisticsAuditEvent
    Base.metadata.create_all(bind=engine)
