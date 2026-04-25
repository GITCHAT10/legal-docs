from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Separate database for United Transfer (Standalone)
UT_DATABASE_URL = os.getenv("UT_DATABASE_URL", "sqlite:///./united_transfer.db")

engine = create_engine(
    UT_DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in UT_DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_ut_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
