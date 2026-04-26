from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from mnos.core.db.base_class import TraceableMixin
import os

DATABASE_URL = "sqlite:///./mnos_dev.db"
if os.getenv("TESTING"):
    DATABASE_URL = "sqlite:///./mnos_test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

class SovereignSession(Session):
    """
    Custom Session: Enforce trace_id on ALL entities before commit.
    Prevents "forgetful" developers from bypassing audit chain.
    """

    def commit(self):
        # Pre-commit validation: ensure every new object has trace_id
        for obj in self.new:
            if isinstance(obj, TraceableMixin):
                if not obj.trace_id:
                    obj.ensure_trace_id()  # Auto-assign if missing

        # Proceed with normal commit
        return super().commit()

SessionLocal = sessionmaker(class_=SovereignSession, autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
