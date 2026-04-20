from sqlalchemy import Column, Integer, String, Enum, JSON, DateTime, ForeignKey, Float
from mnos.core.db.base_class import Base
from datetime import datetime
import enum

class StagingStatus(str, enum.Enum):
    PENDING_PARSE = "pending_parse"
    STAGED = "staged"
    VALIDATION_FAILED = "validation_failed"
    PROMOTED = "promoted"
    FAILED = "failed"

class RoomingListUpload(Base):
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    wholesaler_id = Column(String, index=True) # e.g., "TUI"
    status = Column(Enum(StagingStatus), default=StagingStatus.PENDING_PARSE)
    raw_data = Column(JSON)
    trace_id = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)

class StagingReservation(Base):
    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("roominglistupload.id"))
    guest_name = Column(String)
    check_in = Column(DateTime)
    check_out = Column(DateTime)
    room_type = Column(String)
    occupancy = Column(Integer, default=1)
    total_amount = Column(Float, default=0.0)
    currency = Column(String, default="USD")

    status = Column(Enum(StagingStatus), default=StagingStatus.STAGED)
    row_number = Column(Integer)
    source_file = Column(String)
    validation_errors = Column(JSON)
    parser_stage = Column(String) # e.g., "MAPPING", "TYPE_CONVERSION", "BUSINESS_RULE"
    trace_id = Column(String, unique=True, index=True, nullable=False)

class MappingProfile(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) # e.g., "TUI-Format-V1"
    mapping_config = Column(JSON) # e.g., {"guest_name_col": "Guest", "in_col": "Arrival", "out_col": "Departure", "room_col": "RoomType", "price_col": "Price", "occupancy_col": "Pax"}
