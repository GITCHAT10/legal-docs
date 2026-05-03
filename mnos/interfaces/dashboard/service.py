class DashboardService:
    def __init__(self, shadow, fce, orca):
        self.shadow = shadow
        self.fce = fce
        self.orca = orca

class ExecutiveDashboard(DashboardService):
    def get_summary(self):
        return {
            "project_status": "ACTIVE",
            "budget": "OK",
            "timeline": "ON_TRACK",
            "risk": "LOW",
            "approval_holds": 0,
            "payment_holds": 0
        }

class RCDashboard(DashboardService):
    def get_summary(self):
        return {
            "design_briefs": 5,
            "visual_approvals": 3,
            "render_status": "COMPLETED",
            "design_deviations": 0
        }

class BXDashboard(DashboardService):
    def get_summary(self):
        return {
            "boq": "FINALIZED",
            "contractor_packages": 12,
            "procurement": "ACTIVE",
            "milestones": "4/10",
            "qaqc": "PASSING",
            "handover": "PENDING"
        }

class AXDashboard(DashboardService):
    def get_summary(self):
        return {
            "dredging": "85%",
            "water": "CLASS_A",
            "civil_mep_energy": "VALIDATED",
            "floating": "STABLE",
            "pool": "REEF_SAFE",
            "utilities": "ZERO_LEAK"
        }

class MNOSAuditDashboard(DashboardService):
    def get_summary(self):
        return {
            "aegis_actors": len(set(e["actor_id"] for e in self.shadow.chain)),
            "shadow_chain": len(self.shadow.chain),
            "orca_validations": sum(1 for e in self.shadow.chain if e["event_type"].startswith("orca.validation.")),
            "fce_settlements": sum(1 for e in self.shadow.chain if e["event_type"] == "buildx.fce.settlement.completed"),
            "failed_validations": sum(1 for e in self.shadow.chain if e["event_type"].startswith("orca.validation.") and not e["payload"].get("passed"))
        }
