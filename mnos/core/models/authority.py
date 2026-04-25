from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime
from mnos.core.db.base_class import Base

class AuthorityLease(Base):
    """
    Byzantine Conflict Guard: Edge nodes must renew authority with HK-Hub.
    Lease duration: 12 hours.
    """
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_renewed_at = Column(DateTime, default=datetime.utcnow)

def renew_node_lease(db, node_id: str):
    lease = db.query(AuthorityLease).filter(AuthorityLease.node_id == node_id).first()
    if not lease:
        lease = AuthorityLease(node_id=node_id, expires_at=datetime.utcnow() + timedelta(hours=12))
        db.add(lease)
    else:
        lease.expires_at = datetime.utcnow() + timedelta(hours=12)
        lease.last_renewed_at = datetime.utcnow()
    db.commit()
    return lease

def verify_node_authority(db, node_id: str) -> bool:
    lease = db.query(AuthorityLease).filter(AuthorityLease.node_id == node_id).first()
    if not lease:
        return False
    return lease.expires_at > datetime.utcnow()
