from typing import Generator, Any
from fastapi import Depends, HTTPException, status
from mnos.core.db.session import SessionLocal
from mnos.core.models.user import User

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(
    db = Depends(get_db)
) -> User:
    # Stub for RC1 boot
    user = db.query(User).first()
    if not user:
        # Return a mock user for staging boot tests if DB is empty
        return User(id=1, email="admin@nexus.mv", is_active=True, is_superuser=True)
    return user
