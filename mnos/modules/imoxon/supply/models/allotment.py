from sqlalchemy import Column, Integer, Date, DateTime, String, func
from .contract import Base

class AllotmentBlock(Base):
    __tablename__ = "allotment_blocks"
    block_id = Column(String(50), primary_key=True)
    contract_id = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_units = Column(Integer, nullable=False)      # rooms/seats/slots
    reserved_units = Column(Integer, default=0)
    release_date = Column(DateTime, nullable=True)     # auto-release to open market
    version = Column(Integer, default=0, server_default="1")  # optimistic lock
