from typing import Dict, Any

class SceneRegistry:
    def __init__(self, state_manager):
        self.scenes: Dict[str, Dict[str, Any]] = {}
        self.state_manager = state_manager

    def register_scene(self, name: str, states: Dict[str, Any]):
        self.scenes[name] = states

    def activate_scene(self, name: str):
        if name in self.scenes:
            print(f"🎬 ACTIVATING SCENE: {name}")
            for entity_id, state in self.scenes[name].items():
                self.state_manager.set_state(entity_id, state)

class MQTTAbstraction:
    """
    MQTT-ready communication layer.
    Structure: mnos/iot/<location>/<device_id>/<entity_id>/set
    """
    @staticmethod
    def get_topic(location: str, device_id: str, entity_id: str) -> str:
        return f"mnos/iot/{location}/{device_id}/{entity_id}"

    @staticmethod
    def parse_topic(topic: str) -> Dict[str, str]:
        parts = topic.split("/")
        return {
            "location": parts[2],
            "device_id": parts[3],
            "entity_id": parts[4]
        }
