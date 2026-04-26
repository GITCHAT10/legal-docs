from typing import Any
from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.declarative import as_declarative, declared_attr
import uuid
from datetime import datetime, UTC

@as_declarative()
class Base:
    id: Any
    __name__: str

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

class TraceableMixin:
    """
    Universal mixin: Every entity MUST have trace_id before DB commit.
    Enforced at ORM level + application layer.
    """
    trace_id = Column(
        String, # Use String for SQLite compatibility in sandbox
        default=lambda: str(uuid.uuid4()),
        nullable=False,
        unique=True,
        index=True,
        comment="Cryptographic trace identifier for sovereign audit chain"
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False
    )

    def ensure_trace_id(self):
        """Idempotent trace_id assignment. Call before db.add()."""
        if not self.trace_id:
            self.trace_id = str(uuid.uuid4())
        return self.trace_id
