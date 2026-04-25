from sqlalchemy import Column, String, Float, JSON, Boolean, DateTime, ForeignKey
from mnos.db.schema import Base
import uuid

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
