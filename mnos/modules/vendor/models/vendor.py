from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from mnos.core.db.base_class import Base

class Vendor(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String) # e.g. "Catering", "Fuel", "Maintenance"
    contact_info = Column(JSON)

class BillOfQuantities(Base):
    id = Column(Integer, primary_key=True, index=True)
    project_ref = Column(String, index=True)
    items = Column(JSON) # List of materials/services
    total_estimated_cost = Column(Float)
    status = Column(String, default="draft")
