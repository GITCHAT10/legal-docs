from typing import Dict, Any, List
from mnos.shared.execution_guard import guard
from mnos.core.events.service import events
from mnos.core.security.apollo import apollo

class SecurityModule:
    """
    Sovereign Security Module:
    Handles automated reactions like lockdown, alerts, and door security.
    Enforces 'Never block safe exit from inside'.

    RoE Matrix (Sala Fushi):
    TL-1 Monitor: Known Staff/Guest
    TL-2 Verification: Unknown Person
    TL-3 Alert: Loitering > 180s
    TL-4 Enforcement: Breach of Restricted Zone
    TL-5 Critical: System Interference
    """

    def evaluate_threat(self, event_payload: Dict[str, Any]) -> int:
        """
        Evaluates threat level based on event data and RoE logic.
        """
        frigate_after = event_payload.get("frigate_event", {}).get("after", {})
        confidence = frigate_after.get("confidence", 0)
        label = frigate_after.get("label", "")
        duration = frigate_after.get("duration", 0) # Assumed field from Frigate
        zones = frigate_after.get("current_zones", [])

        # TL-5 Critical: Blindness/Jamming (Simplified detection)
        if frigate_after.get("is_blinded") or frigate_after.get("signal_lost"):
            return 5

        # TL-4 Enforcement: Breach of Restricted Zone
        if "Restricted_Staff_Only" in zones:
            return 4

        # TL-3 Alert: Loitering > 180s in Perimeter
        if "Sala_Fushi_Perimeter" in zones and duration > 180:
            return 3

        # TL-2 Verification: Unknown Person (Public Beach/Perimeter)
        if "Sala_Fushi_Perimeter" in zones and confidence > 0.70:
            # In a real system, we'd check against a face/ID DB here
            is_known = frigate_after.get("is_known", False)
            if not is_known:
                return 2

        # TL-1 Monitor: Known/General awareness
        return 1

    def execute_TL3_response(self, payload: Dict[str, Any]):
        """Toggle Perimeter Lighting to 100%; Audio Warning."""
        print(f"[Security] TL-3 RESPONSE for zone: {payload.get('zone')}")
        print(f"[Security] ACTION: Lighting set to 100%. Audio warning broadcast.")

        # Level 10 Enforcement: Twin-Reporting Metadata
        return {
            "lighting": "100%",
            "audio": "active",
            "reporting_metadata": payload.get("reporting_metadata")
        }

    def execute_TL4_response(self, payload: Dict[str, Any]):
        """Lock Guest Wing Elevators; Send Alert; Capture 4K Still."""
        print(f"[Security] TL-4 RESPONSE for zone: {payload.get('zone')}")
        print(f"[Security] ACTION: Guest Wing Elevators ENTRY RESTRICTED. EXIT ENABLED.")
        print(f"[Security] ACTION: 4K Forensic Still captured.")

        # Level 10 Enforcement: Twin-Reporting Metadata
        return {
            "elevators": "restricted_entry",
            "safe_exit": True,
            "forensic_still": "captured",
            "reporting_metadata": payload.get("reporting_metadata")
        }

    def execute_TL5_response(self, payload: Dict[str, Any]):
        """Total Lockdown: Emergency Egress Alarms; Broadcast to MIG Command Center."""
        print(f"[Security] TL-5 RESPONSE: SYSTEM INTERFERENCE DETECTED")
        print(f"[Security] ACTION: TOTAL LOCKDOWN (ENTRY RESTRICTED). EMERGENCY EGRESS ALARMS ACTIVE.")

        # Level 10 Enforcement: Twin-Reporting Metadata
        return {
            "lockdown": "full_perimeter_entry",
            "alarms": "active",
            "reporting_metadata": payload.get("reporting_metadata")
        }

    def execute_lockdown(self, payload: Dict[str, Any]):
        """General Entry Restriction. PRESERVES SAFE EXIT."""
        print(f"[Security] LOCKDOWN INITIATED for zone: {payload.get('zone')}")
        print(f"[Security] ACTION: Perimeter doors ENTRY RESTRICTED. EXIT REMAINS OPEN.")
        return {"status": "locked", "restriction": "entry_only", "safe_exit": True}

    def trigger_alert(self, payload: Dict[str, Any]):
        """Broadcasts alerts to staff and operators."""
        print(f"[Security] ALERT: {payload.get('message')}")
        return {"status": "alerted", "notified": ["staff", "operators"]}

    def process_security_event(self, event_data: Dict[str, Any], session_context: Dict[str, Any]):
        """
        Main entry point for security events from bridge.
        Route: Bridge -> SecurityModule -> APOLLO -> ExecutionGuard
        """
        try:
            threat_level = self.evaluate_threat(event_data)
        except Exception as e:
            # P1: Fail-Closed Default
            print(f"[Security] EVALUATION FAILURE: {e}. Defaulting to TL-4 Restricted Zone Lockdown.")
            threat_level = 4

        frigate_after = event_data.get("frigate_event", {}).get("after", {})
        zone = frigate_after.get("current_zones", ["unknown"])[0]

        # Level 10 Enforcement: Twin-Reporting Metadata support
        reporting_metadata = event_data.get("reporting_metadata", {
            "reporting_currency_usd": "USD",
            "reporting_currency_local": "MVR",
            "reporting_jurisdiction": "MV"
        })

        # Mandatory Policy Evaluation via APOLLO Control Plane
        if not apollo.evaluate_action(threat_level, zone, event_data):
            print(f"[Security] ACTION BLOCKED BY APOLLO POLICY PLANE")
            return

        if threat_level == 5:
             guard.execute_sovereign_action(
                "nexus.security.lockdown",
                {
                    "zone": "SYSTEM",
                    "threat_level": 5,
                    "detection_source": "Frigate_v1",
                    "evaluated_rule": "System_Interference",
                    "chosen_action": "TL5_Lockdown",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "reporting_metadata": reporting_metadata
                },
                session_context,
                self.execute_TL5_response
            )
        elif threat_level == 4:
            guard.execute_sovereign_action(
                "nexus.security.lockdown",
                {
                    "zone": zone,
                    "threat_level": 4,
                    "detection_source": "Frigate_v1",
                    "evaluated_rule": "Restricted_Zone_Breach",
                    "chosen_action": "TL4_Elevator_Restriction",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "reporting_metadata": reporting_metadata
                },
                session_context,
                self.execute_TL4_response
            )
        elif threat_level == 3:
            guard.execute_sovereign_action(
                "nexus.security.alert",
                {
                    "message": f"TL-3 Alert in {zone}. Lighting and Audio active.",
                    "zone": zone,
                    "detection_source": "Frigate_v1",
                    "evaluated_rule": "Loitering_Threshold",
                    "chosen_action": "TL3_Deterrence",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "reporting_metadata": reporting_metadata
                },
                session_context,
                self.execute_TL3_response
            )
        elif threat_level == 2:
            guard.execute_sovereign_action(
                "nexus.security.alert",
                {"message": f"TL-2 Verification needed in {zone}. Person detected.", "zone": zone},
                session_context,
                self.trigger_alert
            )
        else:
            # TL-1 Monitor
            print(f"[Security] TL-1: Monitoring {zone}")

security_module = SecurityModule()
