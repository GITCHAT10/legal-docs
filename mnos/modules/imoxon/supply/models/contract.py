from sqlalchemy import Column, String, Date, Numeric, Boolean, Enum as SAEnum, func, JSON
from sqlalchemy.orm import declarative_base
import enum

Base = declarative_base()

class ContractStatus(enum.Enum):
    ACTIVE = "active"
    STOP_SALE = "stop_sale"
    EXPIRED = "expired"

class VendorContract(Base):
    __tablename__ = "vendor_contracts"
    contract_id = Column(String(50), primary_key=True)
    vendor_code = Column(String(50), nullable=False)
    product_type = Column(String(20), nullable=False)  # accommodation | transfer | activity
    rate_plan = Column(JSON, nullable=False)          # {base_usd: 150.00, commission_pct: 0.12, currency: "USD"}
    validity_start = Column(Date, nullable=False)
    validity_end = Column(Date, nullable=False)
    status = Column(SAEnum(ContractStatus), default=ContractStatus.ACTIVE)
    updated_at = Column(Date, server_default=func.now())
