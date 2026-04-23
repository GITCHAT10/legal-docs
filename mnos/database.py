from sqlalchemy import create_engine, Column, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./mnos.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class EventLogModel(Base):
    __tablename__ = "event_ingest_log"
    id = Column(String, primary_key=True)
    payload = Column(JSON)
    status = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class IdempotencyRegistryModel(Base):
    __tablename__ = "idempotency_registry"
    key = Column(String, primary_key=True)
    body_hash = Column(String)
    response_json = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ShadowLogModel(Base):
    __tablename__ = "shadow_ledger"
    id = Column(String, primary_key=True)
    event_type = Column(String)
    payload = Column(JSON)
    previous_hash = Column(String)
    current_hash = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_mnos_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
