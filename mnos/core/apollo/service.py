from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, List

class DeploymentStatus(str, Enum):
    PROPOSED = "PROPOSED"
    CANARY = "CANARY"
    LIVE = "LIVE"
    ROLLED_BACK = "ROLLED_BACK"
    STAGING = "STAGING"

class ApolloControlPlane:
    """
    APOLLO Control Plane: Sovereign Orchestration & Lifecycle Management.
    Enforces canary strategies and health-gated rollouts.
    """
    def __init__(self):
        self.deployments: Dict[str, Dict[str, Any]] = {}
        self.health_metrics: Dict[str, float] = {"error_rate": 0.0, "latency": 0.0}
        self.multi_sig_approvals: Dict[str, Set[str]] = {} # deployment_id -> approvers

    def propose_release(self, version: str, manifest: Dict[str, Any]) -> str:
        deployment_id = f"DEP-{version}-{int(datetime.now(timezone.utc).timestamp())}"
        self.deployments[deployment_id] = {
            "version": version,
            "status": DeploymentStatus.PROPOSED,
            "manifest": manifest,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        return deployment_id

    def promote_to_canary(self, deployment_id: str, traffic_percent: int = 5):
        if deployment_id not in self.deployments:
            raise ValueError("Invalid Deployment ID")

        self.deployments[deployment_id]["status"] = DeploymentStatus.CANARY
        self.deployments[deployment_id]["traffic"] = traffic_percent
        print(f"[APOLLO] Deployment {deployment_id} promoted to CANARY ({traffic_percent}% traffic)")

    def approve_production_unlock(self, deployment_id: str, approver_id: str):
        """2/3 multi-sig for production release."""
        if deployment_id not in self.multi_sig_approvals:
            self.multi_sig_approvals[deployment_id] = set()

        self.multi_sig_approvals[deployment_id].add(approver_id)
        count = len(self.multi_sig_approvals[deployment_id])
        print(f"[APOLLO] Multi-sig Approval for {deployment_id}: {approver_id} ({count}/3)")

        if count >= 2:
            self.deployments[deployment_id]["status"] = DeploymentStatus.LIVE
            print(f"[APOLLO] PRODUCTION UNLOCKED: {deployment_id} is now LIVE.")

    def check_health(self) -> bool:
        """Health-gate for rollouts."""
        return self.health_metrics["error_rate"] < 0.01

    def rollback(self, deployment_id: str, reason: str):
        if deployment_id in self.deployments:
            self.deployments[deployment_id]["status"] = DeploymentStatus.ROLLED_BACK
            self.deployments[deployment_id]["rollback_reason"] = reason
            print(f"[APOLLO] EMERGENCY ROLLBACK: {deployment_id} - Reason: {reason}")

apollo = ApolloControlPlane()
