from sqlalchemy import Column, String, Enum, JSON
from skyfarm.database import Base
import enum

class Role(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    CAPTAIN = "captain"
    FARMER = "farmer"

class EntityType(str, enum.Enum):
    VESSEL = "vessel"
    FACILITY = "facility"
    BUSINESS = "business"

class UserModel(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    role = Column(String)
    org_id = Column(String)

class EntityModel(Base):
    __tablename__ = "entities"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    type = Column(String)
    owner_id = Column(String)
    metadata_json = Column(JSON, default={})
