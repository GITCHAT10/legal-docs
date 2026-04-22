from typing import Dict, Any

class MarsSceneEngine:
    """
    MARS SCENE ENGINE: Unified control of device groups.
    Triggered by Context or API.
    """
    def __init__(self, state_manager):
        self.scenes: Dict[str, Dict[str, Any]] = {}
        self.state_manager = state_manager

    def register_scene(self, name: str, states: Dict[str, Any]):
        self.scenes[name] = states

    def activate_scene(self, name: str, location: str):
        if name in self.scenes:
            print(f"🎬 ACTIVATING MARS SCENE: {name} in {location}")
            for entity_suffix, state in self.scenes[name].items():
                entity_id = f"{location}_{entity_suffix}"
                self.state_manager.set_state(entity_id, state)

    def get_standard_scenes(self) -> Dict[str, Dict[str, Any]]:
        return {
            "Welcome Mode": {"light": "ON", "ac": "22C", "curtains": "OPEN"},
            "Night Mode": {"light": "OFF", "ac": "24C", "curtains": "CLOSED"},
            "Emergency Mode": {"light": "PULSE_RED", "ac": "OFF", "curtains": "OPEN"}
        }
