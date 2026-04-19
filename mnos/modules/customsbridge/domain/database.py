from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from mnos.modules.customsbridge.app.config import settings
from mnos.modules.customsbridge.domain.models import Base

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
