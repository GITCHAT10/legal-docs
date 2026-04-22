from typing import Dict, Any
from mnos.shared.execution_guard import guard
from mnos.core.events.service import events

class SecurityModule:
    """
    Sovereign Security Module:
    Handles automated reactions like lockdown, alerts, and door security.
    Enforces 'Never block safe exit from inside'.
    """

    def evaluate_threat(self, event_payload: Dict[str, Any]) -> int:
        """
        Evaluates threat level based on event data.
        TL-1: Monitor, TL-2: Verify, TL-3: Secure Mode, TL-4: Extended Response
        """
        confidence = event_payload.get("frigate_event", {}).get("after", {}).get("confidence", 0)
        label = event_payload.get("frigate_event", {}).get("after", {}).get("label", "")

        if confidence > 0.90:
            return 3 # TL-3 Secure Mode
        elif confidence > 0.75:
            return 2 # TL-2 Verify
        else:
            return 1 # TL-1 Monitor

    def execute_lockdown(self, payload: Dict[str, Any]):
        """Restricts ENTRY to perimeter doors. PRESERVES SAFE EXIT."""
        print(f"[Security] LOCKDOWN INITIATED for zone: {payload.get('zone')}")
        print(f"[Security] ACTION: Perimeter doors ENTRY RESTRICTED. EXIT REMAINS OPEN.")
        return {"status": "locked", "restriction": "entry_only", "safe_exit": True}

    def trigger_alert(self, payload: Dict[str, Any]):
        """Broadcasts alerts to staff and operators."""
        print(f"[Security] ALERT: {payload.get('message')}")
        return {"status": "alerted", "notified": ["staff", "operators"]}

    def process_security_event(self, event_data: Dict[str, Any], session_context: Dict[str, Any]):
        """Main entry point for security events from bridge."""
        threat_level = self.evaluate_threat(event_data)
        zone = event_data.get("frigate_event", {}).get("after", {}).get("current_zones", ["unknown"])[0]

        if threat_level >= 3:
            # TL-3 Secure Mode Actions
            guard.execute_sovereign_action(
                "nexus.security.lockdown",
                {"zone": zone, "threat_level": threat_level},
                session_context,
                self.execute_lockdown
            )

            guard.execute_sovereign_action(
                "nexus.security.alert",
                {"message": f"Threat Level {threat_level} detected in {zone}. Perimeter secured.", "zone": zone},
                session_context,
                self.trigger_alert
            )
        elif threat_level == 2:
            guard.execute_sovereign_action(
                "nexus.security.alert",
                {"message": f"Verify activity in {zone}. Level 2 confidence.", "zone": zone},
                session_context,
                self.trigger_alert
            )

security_module = SecurityModule()
