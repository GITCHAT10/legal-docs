from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = "sqlite:///./mnos_dev.db"
if os.getenv("TESTING"):
    DATABASE_URL = "sqlite:///./mnos_test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
