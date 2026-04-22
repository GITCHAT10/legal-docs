from typing import List, Dict, Any

class MarsAutomationEngine:
    def __init__(self, state_manager):
        self.state_manager = state_manager
        self.rules: List[Dict[str, Any]] = []

    def add_rule(self, name: str, condition_entity: str, condition_state: Any, action_entity: str, action_state: Any):
        self.rules.append({
            "name": name,
            "condition_entity": condition_entity,
            "condition_state": condition_state,
            "action_entity": action_entity,
            "action_state": action_state
        })

    def handle_event(self, data: Dict[str, Any]):
        entity_id = data.get("entity_id")
        new_state = data.get("new_state", {}).get("state")

        for rule in self.rules:
            if rule["condition_entity"] == entity_id and rule["condition_state"] == new_state:
                print(f"🤖 MARS AUTOMATION TRIGGERED: {rule['name']}")
                self.state_manager.set_state(rule["action_entity"], rule["action_state"])

class MarsSceneEngine:
    def __init__(self, state_manager):
        self.scenes: Dict[str, Dict[str, Any]] = {}
        self.state_manager = state_manager

    def register_scene(self, name: str, states: Dict[str, Any]):
        self.scenes[name] = states

    def activate_scene(self, name: str):
        if name in self.scenes:
            print(f"🎬 ACTIVATING MARS SCENE: {name}")
            for entity_id, state in self.scenes[name].items():
                self.state_manager.set_state(entity_id, state)
