from sqlalchemy.orm import Session
from ..models.database import RetailHardwareNode, RetailSessionEvent, RetailSessionCartItem, RetailSession
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import json
import uuid

TRUST_STALE_WINDOW = timedelta(minutes=5)

async def get_hardware_trust_score(db: Session, node_identifier: str) -> Decimal:
    node = db.query(RetailHardwareNode).filter(RetailHardwareNode.node_identifier == node_identifier).first()
    if not node:
        return Decimal("0.5000") # Untrusted if unknown

    # Check freshness
    if node.last_heartbeat_at:
        now = datetime.now(timezone.utc)
        if now - node.last_heartbeat_at > TRUST_STALE_WINDOW:
            return node.trust_score * Decimal("0.8000") # Degrade if stale

    return node.trust_score

async def detect_anomalies(db: Session, session_id: str, event_payload: dict) -> List[str]:
    flags = []
    session_uuid = uuid.UUID(session_id)

    # 1. Burst detection (too many events in short time)
    now = datetime.now(timezone.utc)
    one_minute_ago = now - timedelta(minutes=1)
    recent_events_count = db.query(RetailSessionEvent).filter(
        RetailSessionEvent.session_id == session_uuid,
        RetailSessionEvent.created_at >= one_minute_ago
    ).count()

    if recent_events_count > 20:
        flags.append("ABNORMAL_BURST_SEQUENCE")

    # 2. Impossible cart transitions (e.g. PUT item not in cart)
    if event_payload.get("event_type") == "PUT":
        product_id = event_payload.get("product_id")
        cart_item = db.query(RetailSessionCartItem).filter(
            RetailSessionCartItem.session_id == session_uuid,
            RetailSessionCartItem.product_id == product_id
        ).first()
        if not cart_item or cart_item.qty < Decimal(str(event_payload.get("qty", 0))):
            flags.append("IMPOSSIBLE_PUT_TRANSITION")

    # 3. Duplicate/Replay detection (simplified)
    # In production, check for matching payload + timestamp hashes

    return flags

async def update_hardware_heartbeat(db: Session, node_identifier: str):
    node = db.query(RetailHardwareNode).filter(RetailHardwareNode.node_identifier == node_identifier).first()
    if node:
        node.last_heartbeat_at = datetime.now(timezone.utc)
        node.last_seen_at = datetime.now(timezone.utc)
        db.commit()
