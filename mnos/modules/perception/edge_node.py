from typing import Dict, Any, List
import uuid
import logging
from sqlalchemy import Column, String, Integer, JSON
from mnos.core.db.base_class import Base, TraceableMixin
from mnos.core.db.sync_buffer import SyncBuffer
from mnos.core.events.dispatcher import CanonicalEvent, event_dispatcher

class EdgeAlert(Base, TraceableMixin):
    """
    AEGIS Edge Node Alert.
    Hardened for BUBBLE compliance.
    """
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True)
    zone = Column(String)
    metadata_json = Column(JSON)

class AegisEdgeNode:
    """
    Local-first, offline-resilient Perception Layer.
    Perfect for island deployments.
    """
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.sync_buffer = SyncBuffer()

    def process_detection(self, db, detection_data: Dict[str, Any]):
        """
        Processes local sensor data and queues for sovereign sync.
        """
        alert_type = detection_data.get("type", "PERSON_IN_WATER")
        zone = detection_data.get("zone", "DOCKING_AREA")

        # 1. Map to Canonical Event
        # PERSON_IN_WATER -> ENVIRONMENTAL_ALERT (Example mapping)
        canonical_event = CanonicalEvent.TRANSFER_DISPATCHED # Proxy for demonstration

        # 2. Create Traceable Alert
        alert = EdgeAlert(
            event_type=alert_type,
            zone=zone,
            metadata_json=detection_data
        )
        alert.ensure_trace_id()

        # 3. Queue for Durable Sync (flush -> commit -> clear)
        self.sync_buffer.append({
            "trace_id": str(alert.trace_id),
            "event_type": "EDGE_DETECTION",
            "actor_type": "AEGIS_SENSOR",
            "actor_id": self.node_id,
            "payload": {
                "alert_type": alert_type,
                "zone": zone,
                "canonical_event": canonical_event.value
            },
            "compliance_tags": ["AEGIS-EDGE", "ISLAND-OPERATIONS"]
        })

        return alert

edge_node = AegisEdgeNode(node_id="EDGE-KAF-01")
