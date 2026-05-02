from sqlalchemy import Column, String, Float, JSON, Boolean, DateTime, ForeignKey
from mnos.db.schema import Base
from datetime import datetime, UTC

class ImoxonSupplier(Base):
    __tablename__ = 'imoxon_suppliers'
    id = Column(String(50), primary_key=True)
    name = Column(String(150))
    type = Column(String(30)) # GLOBAL, LOCAL
    kyc_status = Column(String(30))

class ImoxonCatalogProduct(Base):
    __tablename__ = 'imoxon_catalog'
    id = Column(String(50), primary_key=True)
    supplier_id = Column(String(50))
    name = Column(String(150))
    base_price = Column(Float)
    landed_cost = Column(Float)
    status = Column(String(30))

class ImoxonOrder(Base):
    __tablename__ = 'imoxon_orders'
    id = Column(String(50), primary_key=True)
    buyer_id = Column(String(50))
    items = Column(JSON)
    pricing = Column(JSON)
    status = Column(String(30))

class ImoxonWarehouseStock(Base):
    __tablename__ = 'imoxon_warehouse_stock'
    id = Column(String(50), primary_key=True)
    product_id = Column(String(50))
    quantity = Column(Float)
    location = Column(String(50))

class Owner(Base):
    __tablename__ = 'owners'
    id = Column(String(50), primary_key=True)
    legal_name = Column(String(150), nullable=False)
    national_id = Column(String(50))
    tin = Column(String(50))
    bank_account = Column(String(100))
    mars_wallet_id = Column(String(100))
    kyc_status = Column(String(30), default='PENDING')

class Vendor(Base):
    __tablename__ = 'vendors'
    id = Column(String(50), primary_key=True)
    owner_id = Column(String(50), ForeignKey('owners.id'))
    name = Column(String(150), nullable=False)
    island = Column(String(50), nullable=False)
    vendor_type = Column(String(50)) # CAFE, GUESTHOUSE, SHOP
    mars_fee_percent = Column(Float, default=4.0)
    ngo_fee_percent = Column(Float, default=2.0)
    active = Column(Boolean, default=True)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(String(50), primary_key=True)
    guest_id = Column(String(50))
    vendor_id = Column(String(50), ForeignKey('vendors.id'))
    base_amount = Column(Float)
    service_charge = Column(Float)
    tgst = Column(Float)
    green_tax = Column(Float, default=0.0)
    total_amount = Column(Float)
    status = Column(String(30))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

class SettlementSplit(Base):
    __tablename__ = 'settlement_splits'
    id = Column(String(50), primary_key=True)
    order_id = Column(String(50), ForeignKey('orders.id'))
    vendor_amount = Column(Float)
    mars_fee = Column(Float)
    ngo_fee = Column(Float)
    tax_vault_amount = Column(Float)
    payout_status = Column(String(30), default='PENDING')
