from uuid import UUID, uuid4
from decimal import Decimal
from typing import List, Dict, Optional
from mnos.modules.mios.schemas.models import CargoItem, CargoDWS, Container, Shipment

class SkyGodownEngine:
    def __init__(self, shadow):
        self.shadow = shadow
        self.cargo_items: Dict[UUID, CargoItem] = {}
        self.containers: Dict[UUID, Container] = {}
        self.shipments: Dict[UUID, Shipment] = {}

    def receive_cargo(self, actor_ctx: dict, shipment_id: UUID, description: str, dws: CargoDWS) -> CargoItem:
        cargo_id = uuid4()

        # Lane logic
        actual_cbm = dws.actual_cbm
        actual_weight = dws.actual_weight_kg
        longest_side = max(dws.length_cm, dws.width_cm, dws.height_cm)
        sides = sorted([dws.length_cm, dws.width_cm, dws.height_cm], reverse=True)

        parcel_eligible = False
        lane = "BLUE" # Standard

        if actual_cbm < Decimal("0.1"):
            parcel_eligible = True
            lane = "ORANGE"

        if (actual_cbm <= Decimal("0.20") and
            actual_weight <= Decimal("30") and
            longest_side <= Decimal("120") and
            sides[1] <= Decimal("80") and
            sides[2] <= Decimal("80")):
            parcel_eligible = True
            lane = "ORANGE"
        else:
            parcel_eligible = False
            if lane == "ORANGE":
                lane = "BLUE"

        if actual_cbm >= Decimal("2.0") or actual_weight >= Decimal("500"):
            lane = "BLACK" # Project Cargo

        cargo = CargoItem(
            id=cargo_id,
            shipment_id=shipment_id,
            description=description,
            dws=dws,
            cargo_lane=lane,
            parcel_eligible=parcel_eligible
        )

        self.cargo_items[cargo_id] = cargo
        self.shadow.commit("mios.cargo.received", actor_ctx["identity_id"], cargo.dict())
        return cargo

    def create_container(self, actor_ctx: dict, hub_code: str, container_type: str) -> Container:
        container_id = uuid4()
        capacity = Decimal("28") if container_type == "20FT" else Decimal("68")
        container = Container(
            id=container_id,
            hub_code=hub_code,
            type=container_type,
            capacity_cbm=capacity
        )
        self.containers[container_id] = container
        self.shadow.commit("mios.container.created", actor_ctx["identity_id"], container.dict())
        return container

    def assign_to_container(self, actor_ctx: dict, cargo_id: UUID, container_id: UUID):
        cargo = self.cargo_items.get(cargo_id)
        container = self.containers.get(container_id)

        if not cargo or not container:
            raise ValueError("Cargo or Container not found")

        if container.manifest_locked:
            raise ValueError("Container manifest is locked")

        # Check utilization
        current_cbm = sum(c.dws.actual_cbm for c in self.cargo_items.values() if getattr(c, 'container_id', None) == container_id)
        if current_cbm + cargo.dws.actual_cbm > container.capacity_cbm:
            raise ValueError("Container capacity exceeded")

        cargo.container_id = container_id
        self.shadow.commit("mios.cargo.assigned", actor_ctx["identity_id"], {"cargo_id": str(cargo_id), "container_id": str(container_id)})

    def get_container_utilization(self, container_id: UUID) -> Decimal:
        container = self.containers.get(container_id)
        if not container:
            return Decimal("0")

        current_cbm = sum(c.dws.actual_cbm for c in self.cargo_items.values() if getattr(c, 'container_id', None) == container_id)
        return (current_cbm / container.capacity_cbm) * Decimal("100")

    def lock_manifest(self, actor_ctx: dict, container_id: UUID, dispatch_reason: str):
        container = self.containers.get(container_id)
        utilization = self.get_container_utilization(container_id)

        if utilization < Decimal("85") and dispatch_reason == "SKY_GODOWN_SCHEDULE":
            # Godown absorbs dead space
            pass
        elif utilization < Decimal("85") and dispatch_reason == "CUSTOMER_URGENT":
            # Surcharge required - logic handled in FCE
            pass
        elif utilization < Decimal("85"):
            # Could be private project cargo
            pass

        container.manifest_locked = True
        container.dispatch_reason = dispatch_reason
        container.status = "MANIFEST_LOCKED"
        self.shadow.commit("mios.container.manifest_locked", actor_ctx["identity_id"], container.dict())
