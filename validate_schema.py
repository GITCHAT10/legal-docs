import sys
from sqlalchemy import create_engine
from mnos.db.schema import Base

def validate_schema():
    print("🏛️ MNOS SCHEMA VALIDATION")
    try:
        # Use an in-memory sqlite engine for validation
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        print("✅ SQLAlchemy Schema: VALID")
        return True
    except Exception as e:
        print(f"❌ SQLAlchemy Schema: INVALID - {str(e)}")
        return False

if __name__ == "__main__":
    if not validate_schema():
        sys.exit(1)
