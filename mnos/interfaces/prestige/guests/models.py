from sqlalchemy import Column, Integer, String, Date, DateTime, UniqueConstraint
from datetime import datetime, UTC
from mnos.core.db.base_class import Base

class Guest(Base):
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False, default="default")
    trace_id = Column(String, index=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    created_by = Column(String, default="SYSTEM")

    first_name = Column(String, index=True, nullable=False)
    last_name = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False)
    phone = Column(String)
    passport_number = Column(String)
    nationality = Column(String)
    date_of_birth = Column(Date)

    __table_args__ = (UniqueConstraint('tenant_id', 'email', name='_guest_tenant_email_uc'),
                      UniqueConstraint('tenant_id', 'trace_id', name='_guest_tenant_trace_uc'))
