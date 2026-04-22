from typing import List, Dict, Any, Optional

class MarsAutomationEngine:
    """
    MARS INTELLIGENT AUTOMATION: Multi-condition, behavioral triggers.
    Identity-aware (AEGIS) and Context-aware.
    """
    def __init__(self, state_manager, context_engine):
        self.state_manager = state_manager
        self.context_engine = context_engine
        self.rules: List[Dict[str, Any]] = []

    def add_rule(self, name: str, trigger_event: str, conditions: Dict[str, Any], action_entity: str, action_state: Any):
        self.rules.append({
            "name": name,
            "trigger_event": trigger_event,
            "conditions": conditions, # e.g. {"user_id": "GUEST_123", "location": "Room_101"}
            "action_entity": action_entity,
            "action_state": action_state
        })

    def process_event(self, event_type: str, data: Dict[str, Any]):
        location = data.get("location", "global")
        context = self.context_engine.get_context(location)

        for rule in self.rules:
            if rule["trigger_event"] == event_type:
                # Validate multi-conditions against Context (User, Time, State)
                match = True
                for key, val in rule["conditions"].items():
                    if getattr(context, key, None) != val:
                        match = False
                        break

                if match:
                    print(f"🤖 MARS AUTOMATION: Triggering '{rule['name']}' in {location}")
                    self.state_manager.set_state(rule["action_entity"], rule["action_state"])
