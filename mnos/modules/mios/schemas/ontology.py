from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

class MIOSOntology:
    """
    MIOS Palantir-style Ontology Definition
    Entities and Relationships for sovereign import intelligence.
    """

    # Entities
    ENTITIES = [
        "Supplier", "Product", "HS_Code", "Shipment", "Container",
        "Cargo_Item", "Customer", "Broker", "Port", "Freight_Agent",
        "Airline", "Vessel", "UT_Asset", "Payment", "FX_Rate",
        "Handoff", "Risk_Event", "SHADOW_Event"
    ]

    # Relationships
    RELATIONSHIPS = [
        "Supplier supplies Product",
        "Product maps to HS_Code",
        "Product belongs to Shipment",
        "Shipment moves in Container/AWB",
        "Shipment clears through Customs",
        "Shipment pays through FCE",
        "Shipment delivers through UT",
        "Every state change seals through SHADOW"
    ]

class OntologyReference(BaseModel):
    entity_type: str
    entity_id: str
    attributes: dict = {}

class RelationshipLink(BaseModel):
    source_entity: str
    source_id: str
    relation: str
    target_entity: str
    target_id: str
