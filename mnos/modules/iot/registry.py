from typing import Dict, Any, List, Optional
from mnos.modules.iot.models import MarsDeviceSchema, MarsEntitySchema, MarsStateSchema

class MarsDeviceRegistry:
    def __init__(self, shadow_logger):
        self.devices: Dict[str, MarsDeviceSchema] = {}
        self.shadow_logger = shadow_logger

    def register_device(self, device: MarsDeviceSchema):
        self.devices[device.id] = device
        self.shadow_logger.log("MARS_REGISTRY_ADD", {"device_id": device.id})

    def get_device(self, device_id: str) -> Optional[MarsDeviceSchema]:
        return self.devices.get(device_id)

class MarsEntityRegistry:
    def __init__(self):
        self.entities: Dict[str, MarsEntitySchema] = {}

    def register_entity(self, entity: MarsEntitySchema):
        self.entities[entity.id] = entity

class MarsStateManager:
    """
    Sovereign State Manager: Event-driven and Identity-aware.
    """
    def __init__(self, event_bus, shadow_logger):
        self.states: Dict[str, MarsStateSchema] = {}
        self.event_bus = event_bus
        self.shadow_logger = shadow_logger

    def set_state(self, entity_id: str, state: Any, attributes: Optional[Dict] = None):
        old_state = self.states.get(entity_id)
        new_state = MarsStateSchema(entity_id=entity_id, state=state, attributes=attributes or {})
        self.states[entity_id] = new_state

        # Emit MNOS EVENT
        self.event_bus.emit(f"MARS_STATE_CHANGED_{entity_id}", {
            "entity_id": entity_id,
            "old_state": old_state.model_dump() if old_state else None,
            "new_state": new_state.model_dump()
        })

        # Log to MNOS SHADOW
        self.shadow_logger.log("MARS_STATE_CHANGE", {"entity_id": entity_id, "state": state})
