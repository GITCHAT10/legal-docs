from sqlalchemy import Column, String, Float, DateTime, JSON
from skyfarm.database import Base
from datetime import datetime

class RetailSaleModel(Base):
    __tablename__ = "retail_sales"
    id = Column(String, primary_key=True, index=True)
    store_id = Column(String)
    items_json = Column(JSON)
    total_amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
